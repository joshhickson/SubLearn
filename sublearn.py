import argparse
import os
import fetcher
import translator
import merger
import configparser
import sys
import logging

def get_base_path():
    """Get the base path for the application, handling both script and frozen executable."""
    if getattr(sys, 'frozen', False):
        # The application is frozen
        return os.path.dirname(sys.executable)
    else:
        # The application is not frozen
        return os.path.dirname(os.path.abspath(__file__))

def _select_best_dub_subtitle(dub_subs: list, dub_keywords: list) -> dict | None:
    """
    Selects the best dub subtitle from a list based on keywords and download count.
    """
    if not dub_subs:
        return None

    best_dub_sub = None
    max_score = -1

    for sub in dub_subs:
        attrs = sub.get("attributes", {})
        score = 0
        release_name = attrs.get("release", "").lower()
        comments = attrs.get("comments", "").lower()

        if any(keyword in release_name for keyword in dub_keywords): score += 10
        if any(keyword in comments for keyword in dub_keywords): score += 5
        score += attrs.get("download_count", 0) / 10000.0

        if score > max_score:
            max_score = score
            best_dub_sub = sub

    if max_score <= 0:
        best_dub_sub = max(dub_subs, key=lambda s: s.get("attributes", {}).get("download_count", 0))
        final_score_str = f"Downloads: {best_dub_sub.get('attributes', {}).get('download_count', 0)}"
    else:
        final_score_str = f"Score: {max_score:.2f}"

    logging.info(f"Auto-selected dub sub: {best_dub_sub.get('attributes', {}).get('release', 'N/A')} ({final_score_str})")
    return best_dub_sub

def _prompt_for_selection(sub_list: list, sub_type: str) -> dict | None:
    """Displays a list of subtitles and prompts the user to select one."""
    if not sub_list:
        return None

    logging.info(f"\n--- Please select a {sub_type} subtitle ---")
    for i, sub_data in enumerate(sub_list):
        attrs = sub_data.get("attributes", {})
        release = attrs.get("release", "N/A")
        downloads = attrs.get("download_count", 0)
        comments = attrs.get("comments", "No comments").strip().replace("\n", " ")
        logging.info(f"[{i+1}] {release} (Downloads: {downloads})")
        if comments:
            logging.info(f"    Comment: {comments}")

    while True:
        try:
            choice = input(f"Enter number (1-{len(sub_list)}), or 0 to skip: ")
            choice_idx = int(choice) - 1
            if choice_idx == -1: return None
            if 0 <= choice_idx < len(sub_list): return sub_list[choice_idx]
            else: logging.warning("Invalid selection. Please try again.")
        except (ValueError, IndexError):
            logging.warning("Invalid input. Please enter a number.")

def process_video_file(video_path: str, args: argparse.Namespace, api_keys: dict):
    """
    Runs the full SubLearn workflow for a single video file.
    """
    logging.info(f"\n--- Starting processing for: {os.path.basename(video_path)} ---")
    video_filename_no_ext = os.path.splitext(os.path.basename(video_path))[0]
    output_dir = os.path.join(os.path.dirname(video_path), video_filename_no_ext)
    os.makedirs(output_dir, exist_ok=True)
    logging.info(f"Output will be saved to: {output_dir}")

    try:
        orig_sub_path, dub_sub_path = None, None
        logging.info("--- Locating Subtitle Files ---")

        local_orig_path = os.path.join(output_dir, f"{video_filename_no_ext}.{args.lang_orig}.srt")
        if os.path.exists(local_orig_path):
            logging.info(f"Found local original subtitle: {os.path.basename(local_orig_path)}")
            orig_sub_path = local_orig_path
        local_dub_path = os.path.join(output_dir, f"{video_filename_no_ext}.{args.lang_dub}.srt")
        if os.path.exists(local_dub_path):
            logging.info(f"Found local dub subtitle: {os.path.basename(local_dub_path)}")
            dub_sub_path = local_dub_path

        if not orig_sub_path or not dub_sub_path:
            movie_hash = fetcher.get_movie_hash(video_path)
            if not movie_hash:
                logging.error(f"Could not calculate movie hash for {video_filename_no_ext}.")
            else:
                online_orig_subs, online_dub_subs = fetcher.search_subtitles(movie_hash, args.lang_orig, args.lang_dub, api_keys['opensubtitles'])
                if not orig_sub_path and not args.no_orig_search and online_orig_subs:
                    selected_meta = _prompt_for_selection(online_orig_subs, "original") if args.interactive else max(online_orig_subs, key=lambda s: s.get("attributes", {}).get("download_count", 0))
                    if selected_meta:
                        save_path = os.path.join(output_dir, f"{video_filename_no_ext}.{args.lang_orig}.srt")
                        orig_sub_path = fetcher.download_subtitle(selected_meta, api_keys['opensubtitles'], save_path)
                if not dub_sub_path and online_dub_subs:
                    selected_meta = _prompt_for_selection(online_dub_subs, "dub") if args.interactive else _select_best_dub_subtitle(online_dub_subs, ["dub", "dubbed", "szinkron"])
                    if selected_meta:
                        save_path = os.path.join(output_dir, f"{video_filename_no_ext}.{args.lang_dub}.srt")
                        dub_sub_path = fetcher.download_subtitle(selected_meta, api_keys['opensubtitles'], save_path)

        if not dub_sub_path:
            logging.error(f"Could not retrieve dub subtitle for {video_filename_no_ext}. Skipping.")
            return

        logging.info(f"Translating dub file: {os.path.basename(dub_sub_path)}")
        translated_texts = translator.translate_subtitle_file(filepath=dub_sub_path, target_lang=args.lang_native, api_key=api_keys['deepl'])
        if not translated_texts:
            logging.error(f"Could not translate subtitle file for {video_filename_no_ext}. Skipping.")
            return

        output_path = os.path.join(output_dir, f"{video_filename_no_ext}.sublearn.ass")
        merger.create_merged_subtitle_file(dub_sub_path=dub_sub_path, translated_texts=translated_texts, output_path=output_path, orig_sub_path=orig_sub_path)
        logging.info(f"--- Successfully completed processing for: {os.path.basename(video_path)} ---")

    except Exception:
        logging.error(f"An unexpected error occurred while processing {os.path.basename(video_path)}.", exc_info=True)

def main():
    """
    Main function to run the SubLearn command-line interface.
    """
    base_path = get_base_path()

    # --- Logging Setup ---
    log_file_path = os.path.join(base_path, 'sublearn.log')
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename=log_file_path, filemode='w')
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(message)s'))
    logging.getLogger().addHandler(console_handler)

    # --- Configuration Loading ---
    config = configparser.ConfigParser()
    config_path = os.path.join(base_path, 'config.ini')
    if not os.path.exists(config_path):
        logging.error(f"Configuration file '{config_path}' not found. Please create it from the example.")
        sys.exit(1)
    config.read(config_path)
    try:
        api_keys = {
            'opensubtitles': config.get('API_KEYS', 'OPENSUBTITLES_API_KEY'),
            'deepl': config.get('API_KEYS', 'DEEPL_API_KEY')
        }
        if 'YOUR_API_KEY_HERE' in api_keys.values():
            logging.warning("API key in 'config.ini' still has the default placeholder value.")
    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        logging.error(f"Error reading API keys from '{config_path}': {e}", exc_info=True)
        sys.exit(1)

    parser = argparse.ArgumentParser(description="SubLearn: A tool for creating multi-track subtitles for language learning.")
    parser.add_argument("path", help="The full path to the local video file or directory of video files.")
    parser.add_argument("--lang_orig", default="en", help="The original language of the video (e.g., 'en').")
    parser.add_argument("--lang_dub", required=True, help="The language of the dubbed audio track (e.g., 'hu', 'es').")
    parser.add_argument("--lang_native", default="EN-US", help="Your native language for translation (e.g., 'EN-US', 'DE').")
    parser.add_argument("--interactive", action="store_true", help="Enable interactive mode to manually select subtitles.")
    parser.add_argument("--no-orig-search", action="store_true", help="Do not search for an original language subtitle online.")
    args = parser.parse_args()

    # --- Path processing ---
    input_path = args.path
    if os.path.isfile(input_path):
        videos_to_process = [input_path]
    elif os.path.isdir(input_path):
        logging.info(f"Scanning directory for video files: {input_path}")
        supported_extensions = ['.mkv', '.mp4', '.avi', '.mov']
        videos_to_process = [
            os.path.join(input_path, f) for f in os.listdir(input_path)
            if os.path.isfile(os.path.join(input_path, f)) and os.path.splitext(f)[1].lower() in supported_extensions
        ]
        logging.info(f"Found {len(videos_to_process)} video file(s) to process.")
    else:
        logging.error(f"The provided path is not a valid file or directory: {input_path}")
        sys.exit(1)

    for video_path in videos_to_process:
        process_video_file(video_path, args, api_keys)



if __name__ == "__main__":
    main()
