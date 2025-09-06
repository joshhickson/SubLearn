import os
import struct
import requests
import tempfile
import logging

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
        logging.error(f"Error getting download link (status {resp.status_code}): {resp.text}")
        return None

def _download_subtitle_file(url: str, save_path: str | None = None) -> str | None:
    """
    Downloads content from a URL and saves it to a specified path or a temporary SRT file.
    """
    try:
        resp = requests.get(url)
        resp.raise_for_status()

        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(resp.content)
            return save_path
        else:
            fd, temp_path = tempfile.mkstemp(suffix=".srt")
            with os.fdopen(fd, "wb") as f:
                f.write(resp.content)
            return temp_path
    except requests.RequestException as e:
        logging.error(f"Error downloading subtitle file: {e}", exc_info=True)
        return None

def search_subtitles(movie_hash: str, lang_orig: str, lang_dub: str, api_key: str) -> tuple[list, list]:
    """
    Searches for subtitles using the OpenSubtitles API and returns lists of available subs.
    """
    languages_to_search = f"{lang_orig},{lang_dub}"
    logging.info(f"Searching for '{languages_to_search}' subtitles online...")

    headers = {
        "Api-Key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "SubLearn v1.0"
    }
    params = {"moviehash": movie_hash, "languages": languages_to_search}

    try:
        resp = requests.get(f"{API_URL}/subtitles", headers=headers, params=params)
        resp.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Error querying OpenSubtitles API: {e}", exc_info=True)
        return [], []

    data = resp.json().get("data", [])
    if not data:
        logging.warning("No subtitles found for this movie hash.")
        return [], []

    orig_subs = [s for s in data if s.get("attributes", {}).get("language") == lang_orig]
    dub_subs = [s for s in data if s.get("attributes", {}).get("language") == lang_dub]

    logging.info(f"Found {len(orig_subs)} original language subs and {len(dub_subs)} dub language subs.")
    return orig_subs, dub_subs

def download_subtitle(subtitle_data: dict, api_key: str, save_path: str) -> str | None:
    """
    Downloads a subtitle file given its metadata and a destination path.
    """
    headers = {
        "Api-Key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "SubLearn v1.0"
    }
    try:
        file_id = subtitle_data["attributes"]["files"][0]["file_id"]
        link = _get_download_link(file_id, api_key, headers)
        if not link:
            logging.error("Failed to get subtitle download link.")
            return None

        downloaded_path = _download_subtitle_file(link, save_path=save_path)
        if not downloaded_path:
            logging.error("Failed to download subtitle file.")
            return None

        logging.info(f"Subtitle '{os.path.basename(save_path)}' saved successfully.")
        return downloaded_path
    except (KeyError, IndexError) as e:
        logging.error(f"Error parsing subtitle data: {e}", exc_info=True)
        return None

def search_subtitles_by_query(query: str, language: str, api_key: str) -> list:
    """
    Searches for subtitles using a query string (e.g., movie title).
    """
    logging.info(f"Searching for '{language}' subtitles online with query: '{query}'")

    headers = {
        "Api-Key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "SubLearn v1.0"
    }
    params = {"query": query, "languages": language}

    try:
        resp = requests.get(f"{API_URL}/subtitles", headers=headers, params=params)
        resp.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Error querying OpenSubtitles API by query: {e}", exc_info=True)
        return []

    data = resp.json().get("data", [])
    if not data:
        logging.warning(f"No subtitles found for query '{query}' in language '{language}'.")
    else:
        logging.info(f"Found {len(data)} results for query.")

    return data
