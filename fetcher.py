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

def _download_subtitle_file(url: str) -> str | None:
    """Downloads content from a URL and saves it to a temporary SRT file."""
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        # Use a temporary file to store the subtitle
        fd, temp_path = tempfile.mkstemp(suffix=".srt")
        with os.fdopen(fd, 'wb') as f:
            f.write(resp.content)
        return temp_path
    except requests.RequestException as e:
        print(f"Error downloading subtitle file: {e}")
        return None

def find_and_download_subtitles(video_path: str, lang_orig: str, lang_dub: str, api_key: str):
    """
    Finds and downloads original and dub-language subtitles for a video file.
    """
    print("Calculating movie hash...")
    movie_hash = get_movie_hash(video_path)
    if not movie_hash:
        print("Error: Could not calculate movie hash. The file may be invalid, inaccessible, or too small.")
        return None, None

    print(f"Movie hash: {movie_hash}")
    print(f"Searching for '{lang_orig}' and '{lang_dub}' subtitles...")

    headers = {"Api-Key": api_key, "Content-Type": "application/json", "Accept": "application/json"}
    params = {"moviehash": movie_hash, "languages": f"{lang_orig},{lang_dub}"}

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

    # Separate subtitles by language
    orig_subs = [s for s in data if s.get("attributes", {}).get("language") == lang_orig]
    dub_subs = [s for s in data if s.get("attributes", {}).get("language") == lang_dub]

    if not orig_subs:
        print(f"No subtitles found for the original language ({lang_orig}).")
        return None, None
    if not dub_subs:
        print(f"No subtitles found for the dub language ({lang_dub}).")
        return None, None

    # --- Heuristic selection for the DUB subtitle ---
    print(f"Found {len(dub_subs)} subtitle(s) for the dub language. Analyzing...")
    dub_keywords = ["dub", "dubbed", "szinkron"] # As per blueprint, using 'szinkron' as an example

    best_dub_sub = None
    max_score = -1

    for sub in dub_subs:
        attrs = sub.get("attributes", {})
        score = 0
        release_name = attrs.get("release", "").lower()
        comments = attrs.get("comments", "").lower()

        # 1. Analyze release name (+10 points)
        if any(keyword in release_name for keyword in dub_keywords):
            score += 10

        # 2. Search user comments (+5 points)
        if any(keyword in comments for keyword in dub_keywords):
            score += 5

        # 3. Leverage popularity (+1 per 10k downloads)
        score += attrs.get("download_count", 0) / 10000

        if score > max_score:
            max_score = score
            best_dub_sub = sub

    if not best_dub_sub:
        print("Could not determine the best dub subtitle based on heuristics. Falling back to most downloaded.")
        best_dub_sub = max(dub_subs, key=lambda s: s.get("attributes", {}).get("download_count", 0))

    # --- Select ORIGINAL subtitle (most downloaded) ---
    orig_sub = max(orig_subs, key=lambda s: s.get("attributes", {}).get("download_count", 0))

    print(f"Selected original sub: {orig_sub['attributes']['release']} (Downloads: {orig_sub['attributes']['download_count']})")
    print(f"Selected dub sub: {best_dub_sub['attributes']['release']} (Score: {max_score:.2f}, Downloads: {best_dub_sub['attributes']['download_count']})")

    # --- Download the selected files ---
    orig_file_id = orig_sub["attributes"]["files"][0]["file_id"]
    dub_file_id = best_dub_sub["attributes"]["files"][0]["file_id"]

    print("Requesting download links...")
    orig_link = _get_download_link(orig_file_id, api_key, headers)
    dub_link = _get_download_link(dub_file_id, api_key, headers)

    if not orig_link or not dub_link:
        print("Failed to get one or more download links.")
        return None, None

    print("Downloading subtitle files...")
    orig_filepath = _download_subtitle_file(orig_link)
    dub_filepath = _download_subtitle_file(dub_link)

    if not orig_filepath or not dub_filepath:
        print("Failed to download one or more subtitle files.")
        return None, None

    print(f"Original language subtitle saved to: {orig_filepath}")
    print(f"Dub language subtitle saved to: {dub_filepath}")

    return orig_filepath, dub_filepath
