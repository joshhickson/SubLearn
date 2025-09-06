import argparse
import os
import fetcher
import translator
import merger
import configparser
import sys
import logging
import pysubs2

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

def process_video_file(video_path: str, args: argparse.Namespace, api_keys: dict, styles: dict):
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

        # Priority 1: Use files specified in arguments
        if args.orig_file:
            if os.path.exists(args.orig_file):
                logging.info(f"Using user-provided original subtitle: {args.orig_file}")
                orig_sub_path = args.orig_file
            else:
                logging.warning(f"File specified by --orig-file not found: {args.orig_file}")
        if args.dub_file:
            if os.path.exists(args.dub_file):
                logging.info(f"Using user-provided dub subtitle: {args.dub_file}")
                dub_sub_path = args.dub_file
            else:
                logging.warning(f"File specified by --dub-file not found: {args.dub_file}")

        # Priority 2: Auto-detect files in output directory
        if not orig_sub_path:
            local_orig_path = os.path.join(output_dir, f"{video_filename_no_ext}.{args.lang_orig}.srt")
            if os.path.exists(local_orig_path):
                logging.info(f"Found local original subtitle: {os.path.basename(local_orig_path)}")
                orig_sub_path = local_orig_path
        if not dub_sub_path:
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
        merger.create_merged_subtitle_file(
            dub_sub_path=dub_sub_path, translated_texts=translated_texts,
            output_path=output_path, orig_sub_path=orig_sub_path, styles=styles
        )
        logging.info(f"--- Successfully completed processing for: {os.path.basename(video_path)} ---")

    except Exception:
        logging.error(f"An unexpected error occurred while processing {os.path.basename(video_path)}.", exc_info=True)

def load_styles_from_config(config: configparser.ConfigParser) -> dict:
    """Loads subtitle styles from the config parser, with defaults."""
    # Map user-friendly strings to pysubs2 Alignment enums
    alignment_map = {
        "BOTTOM_LEFT": pysubs2.Alignment.BOTTOM_LEFT, "BOTTOM_CENTER": pysubs2.Alignment.BOTTOM_CENTER, "BOTTOM_RIGHT": pysubs2.Alignment.BOTTOM_RIGHT,
        "MIDDLE_LEFT": pysubs2.Alignment.MIDDLE_LEFT, "MIDDLE_CENTER": pysubs2.Alignment.MIDDLE_CENTER, "MIDDLE_RIGHT": pysubs2.Alignment.MIDDLE_RIGHT,
        "TOP_LEFT": pysubs2.Alignment.TOP_LEFT, "TOP_CENTER": pysubs2.Alignment.TOP_CENTER, "TOP_RIGHT": pysubs2.Alignment.TOP_RIGHT,
    }

    styles = {
        'dub_fontsize': 24, 'dub_color': (255, 255, 0), 'dub_alignment': pysubs2.Alignment.TOP_CENTER, 'dub_marginv': 10,
        'trans_fontsize': 22, 'trans_color': (0, 255, 255), 'trans_alignment': pysubs2.Alignment.TOP_CENTER, 'trans_marginv': 40,
        'orig_fontsize': 14, 'orig_color': (255, 255, 255), 'orig_alignment': pysubs2.Alignment.BOTTOM_CENTER, 'orig_marginv': 10,
    }
    if not config.has_section('STYLES'):
        return styles

    def get_style(key, getter, default):
        try:
            return getter('STYLES', key)
        except (configparser.NoOptionError, ValueError):
            logging.warning(f"Could not parse '{key}' from config, using default: {default}")
            return default

    styles['orig_fontsize'] = get_style('orig_fontsize', config.getint, styles['orig_fontsize'])
    styles['dub_fontsize'] = get_style('dub_fontsize', config.getint, styles['dub_fontsize'])
    styles['trans_fontsize'] = get_style('trans_fontsize', config.getint, styles['trans_fontsize'])

    styles['orig_marginv'] = get_style('orig_marginv', config.getint, styles['orig_marginv'])
    styles['dub_marginv'] = get_style('dub_marginv', config.getint, styles['dub_marginv'])
    styles['trans_marginv'] = get_style('trans_marginv', config.getint, styles['trans_marginv'])

    styles['orig_color'] = (get_style('orig_color_r', config.getint, 255), get_style('orig_color_g', config.getint, 255), get_style('orig_color_b', config.getint, 255))
    styles['dub_color'] = (get_style('dub_color_r', config.getint, 255), get_style('dub_color_g', config.getint, 255), get_style('dub_color_b', config.getint, 0))
    styles['trans_color'] = (get_style('trans_color_r', config.getint, 0), get_style('trans_color_g', config.getint, 255), get_style('trans_color_b', config.getint, 255))

    orig_align_str = get_style('orig_alignment', config.get, 'TOP_CENTER').upper()
    dub_align_str = get_style('dub_alignment', config.get, 'MIDDLE_CENTER').upper()
    trans_align_str = get_style('trans_alignment', config.get, 'BOTTOM_CENTER').upper()

    styles['orig_alignment'] = alignment_map.get(orig_align_str, styles['orig_alignment'])
    styles['dub_alignment'] = alignment_map.get(dub_align_str, styles['dub_alignment'])
    styles['trans_alignment'] = alignment_map.get(trans_align_str, styles['trans_alignment'])

    return styles

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

    # Load styles from config
    styles = load_styles_from_config(config)

    parser = argparse.ArgumentParser(description="SubLearn: A tool for creating multi-track subtitles for language learning.")
    parser.add_argument("path", help="The full path to the local video file or directory of video files.")
    parser.add_argument("--lang_orig", default="en", help="The original language of the video (e.g., 'en').")
    parser.add_argument("--lang_dub", required=True, help="The language of the dubbed audio track (e.g., 'hu', 'es').")
    parser.add_argument("--lang_native", default="EN-US", help="Your native language for translation (e.g., 'EN-US', 'DE').")
    parser.add_argument("--interactive", action="store_true", help="Enable interactive mode to manually select subtitles.")
    parser.add_argument("--no-orig-search", action="store_true", help="Do not search for an original language subtitle online.")
    parser.add_argument("--orig-file", help="Path to a local .srt file for the original language track (single file mode only).")
    parser.add_argument("--dub-file", help="Path to a local .srt file for the dub track (single file mode only).")
    args = parser.parse_args()

    # --- Path processing ---
    input_path = os.path.abspath(args.path)
    videos_to_process = []
    is_batch_mode = os.path.isdir(input_path)

    if is_batch_mode:
        if args.orig_file or args.dub_file:
            logging.error("--orig-file and --dub-file cannot be used with a directory path. Please specify a single video file.")
            sys.exit(1)

        logging.info(f"Scanning directory for video files: {input_path}")
        supported_extensions = ['.mkv', '.mp4', '.avi', '.mov']
        videos_to_process = [
            os.path.join(input_path, f) for f in os.listdir(input_path)
            if os.path.isfile(os.path.join(input_path, f)) and os.path.splitext(f)[1].lower() in supported_extensions
        ]
        logging.info(f"Found {len(videos_to_process)} video file(s) to process.")
    elif os.path.isfile(input_path):
        videos_to_process = [input_path]
    else:
        logging.error(f"The provided path is not a valid file or directory: {input_path}")
        sys.exit(1)

    for video_path in videos_to_process:
        process_video_file(video_path, args, api_keys, styles)



if __name__ == "__main__":
    main()
