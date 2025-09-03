import os
import struct
import requests
import tempfile

API_URL = "https://api.opensubtitles.com/api/v1"

def get_movie_hash(file_path: str) -> str:
    """
    Calculate a hash for a video file based on the OpenSubtitles.org algorithm.
    The hash is calculated from the first and last 64kb of the file.
    Reference: https://github.com/OpenSubtitles/OpenSubtitlesAPI/blob/master/src/OpenSubtitlesAPI/Hasher.cs
    """
    try:
        longlongformat = "<q"  # Little-endian, 64-bit
        bytesize = struct.calcsize(longlongformat)

        with open(file_path, "rb") as f:
            filesize = os.path.getsize(file_path)
            hash_value = filesize

            if filesize < 65536 * 2:
                return ""

            # Process first 64kb
            for _ in range(65536 // bytesize):
                buffer = f.read(bytesize)
                (l_value,) = struct.unpack(longlongformat, buffer)
                hash_value += l_value
                hash_value &= 0xFFFFFFFFFFFFFFFF

            # Process last 64kb
            f.seek(max(0, filesize - 65536), 0)
            for _ in range(65536 // bytesize):
                buffer = f.read(bytesize)
                (l_value,) = struct.unpack(longlongformat, buffer)
                hash_value += l_value
                hash_value &= 0xFFFFFFFFFFFFFFFF

        return f"{hash_value:016x}"
    except (IOError, FileNotFoundError):
        return ""

def _get_download_link(file_id: int, api_key: str, headers: dict) -> str | None:
    """Requests the download link for a specific file ID."""
    body = {"file_id": file_id}
    resp = requests.post(f"{API_URL}/download", headers=headers, json=body)
    if resp.status_code == 200:
        return resp.json().get("link")
    else:
        print(f"Error getting download link (status {resp.status_code}): {resp.text}")
        return None

def _download_subtitle_file(url: str, save_path: str | None = None) -> str | None:
    """
    Downloads content from a URL and saves it to a specified path or a temporary SRT file.
    """
    try:
        resp = requests.get(url)
        resp.raise_for_status()

        if save_path:
            # Ensure the directory exists before writing the file
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(resp.content)
            return save_path
        else:
            # Fallback to temporary file if no save_path is provided
            fd, temp_path = tempfile.mkstemp(suffix=".srt")
            with os.fdopen(fd, "wb") as f:
                f.write(resp.content)
            return temp_path
    except requests.RequestException as e:
        print(f"Error downloading subtitle file: {e}")
        return None

def find_and_download_subtitles(
    video_path: str,
    lang_orig: str,
    lang_dub: str,
    api_key: str,
    skip_dub: bool = False,
    skip_orig: bool = False,
    output_dir: str | None = None
):
    """
    Finds and downloads subtitles. Can skip fetching either track if requested.
    If output_dir is provided, subtitles are saved there with a standard name.
    """
    if skip_dub and skip_orig:
        print("Skipping online search for both tracks.")
        return None, None

    print("Calculating movie hash...")
    movie_hash = get_movie_hash(video_path)
    if not movie_hash:
        print("Error: Could not calculate movie hash. The file may be invalid, inaccessible, or too small.")
        return None, None

    print(f"Movie hash: {movie_hash}")
    video_filename_no_ext = os.path.splitext(os.path.basename(video_path))[0]

    languages_to_search = []
    if not skip_orig: languages_to_search.append(lang_orig)
    if not skip_dub: languages_to_search.append(lang_dub)

    print(f"Searching for '{','.join(languages_to_search)}' subtitles online...")
    headers = {"Api-Key": api_key, "Content-Type": "application/json", "Accept": "application/json"}
    params = {"moviehash": movie_hash, "languages": ",".join(languages_to_search)}

    try:
        resp = requests.get(f"{API_URL}/subtitles", headers=headers, params=params)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"Error querying OpenSubtitles API: {e}")
        return None, None

    data = resp.json().get("data", [])
    if not data:
        print("No subtitles found for this movie hash.")
        return None, None

    orig_filepath = None
    dub_filepath = None

    # --- Process Original Language Subtitle ---
    if not skip_orig:
        orig_subs = [s for s in data if s.get("attributes", {}).get("language") == lang_orig]
        if not orig_subs:
            print(f"No subtitles found for the original language ({lang_orig}).")
        else:
            orig_sub_data = max(orig_subs, key=lambda s: s.get("attributes", {}).get("download_count", 0))
            print(f"Selected original sub: {orig_sub_data['attributes']['release']} (Downloads: {orig_sub_data['attributes']['download_count']})")
            orig_file_id = orig_sub_data["attributes"]["files"][0]["file_id"]
            orig_link = _get_download_link(orig_file_id, api_key, headers)
            if not orig_link:
                print("Failed to get original subtitle download link.")
            else:
                orig_save_path = os.path.join(output_dir, f"{video_filename_no_ext}.{lang_orig}.srt") if output_dir else None
                orig_filepath = _download_subtitle_file(orig_link, save_path=orig_save_path)
                if not orig_filepath:
                    print("Failed to download original subtitle file.")
                else:
                    print(f"Original language subtitle saved to: {orig_filepath}")

    # --- Process Dub Language Subtitle ---
    if not skip_dub:
        dub_subs = [s for s in data if s.get("attributes", {}).get("language") == lang_dub]
        if not dub_subs:
            print(f"No subtitles found for the dub language ({lang_dub}).")
        else:
            print(f"Found {len(dub_subs)} subtitle(s) for the dub language. Analyzing...")
            dub_keywords = ["dub", "dubbed", "szinkron"]
            best_dub_sub = None
            max_score = -1
            for sub in dub_subs:
                attrs = sub.get("attributes", {})
                score = 0
                release_name = attrs.get("release", "").lower()
                comments = attrs.get("comments", "").lower()
                if any(keyword in release_name for keyword in dub_keywords): score += 10
                if any(keyword in comments for keyword in dub_keywords): score += 5
                score += attrs.get("download_count", 0) / 10000
                if score > max_score:
                    max_score = score
                    best_dub_sub = sub
            if not best_dub_sub:
                best_dub_sub = max(dub_subs, key=lambda s: s.get("attributes", {}).get("download_count", 0))

            print(f"Selected dub sub: {best_dub_sub['attributes']['release']} (Score: {max_score:.2f}, Downloads: {best_dub_sub['attributes']['download_count']})")
            dub_file_id = best_dub_sub["attributes"]["files"][0]["file_id"]
            dub_link = _get_download_link(dub_file_id, api_key, headers)
            if not dub_link:
                print("Failed to get dub subtitle download link.")
            else:
                dub_save_path = os.path.join(output_dir, f"{video_filename_no_ext}.{lang_dub}.srt") if output_dir else None
                dub_filepath = _download_subtitle_file(dub_link, save_path=dub_save_path)
                if not dub_filepath:
                    print("Failed to download dub subtitle file.")
                else:
                    print(f"Dub language subtitle saved to: {dub_filepath}")

    # If we are using temporary files and only downloaded one of two, clean up.
    if not output_dir:
        if orig_filepath and not dub_filepath and not skip_dub:
             os.remove(orig_filepath) # Clean up temp file
        if not orig_filepath and dub_filepath and not skip_orig:
             os.remove(dub_filepath) # Clean up temp file


    return orig_filepath, dub_filepath
