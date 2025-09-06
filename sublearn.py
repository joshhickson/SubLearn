import argparse
import os
import fetcher
import translator
import merger
import transcriber
import aligner  # Import new module
import configparser
import sys
import re
import logging
import pysubs2
import tempfile

def get_base_path():
    """Get the base path for the application, handling both script and frozen executable."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def _select_best_dub_subtitle(dub_subs: list, dub_keywords: list) -> dict | None:
    """Selects the best dub subtitle from a list based on keywords and download count."""
    if not dub_subs: return None
    best_dub_sub, max_score = None, -1
    for sub in dub_subs:
        attrs = sub.get("attributes", {})
        score = 0
        release_name = attrs.get("release", "").lower()
        comments = attrs.get("comments", "").lower()
        if any(keyword in release_name for keyword in dub_keywords): score += 10
        if any(keyword in comments for keyword in dub_keywords): score += 5
        score += attrs.get("download_count", 0) / 10000.0
        if score > max_score:
            max_score, best_dub_sub = score, sub
    if max_score <= 0:
        best_dub_sub = max(dub_subs, key=lambda s: s.get("attributes", {}).get("download_count", 0))
        final_score_str = f"Downloads: {best_dub_sub.get('attributes', {}).get('download_count', 0)}"
    else:
        final_score_str = f"Score: {max_score:.2f}"
    logging.info(f"Auto-selected dub sub: {best_dub_sub.get('attributes', {}).get('release', 'N/A')} ({final_score_str})")
    return best_dub_sub

def _prompt_for_selection(sub_list: list, sub_type: str) -> dict | None:
    """Displays a list of subtitles and prompts the user to select one."""
    if not sub_list: return None
    logging.info(f"\n--- Please select a {sub_type} subtitle ---")
    for i, sub_data in enumerate(sub_list):
        attrs = sub_data.get("attributes", {})
        release = attrs.get("release", "N/A")
        downloads = attrs.get("download_count", 0)
        comments = attrs.get("comments", "No comments").strip().replace("\n", " ")
        logging.info(f"[{i+1}] {release} (Downloads: {downloads})")
        if comments: logging.info(f"    Comment: {comments}")
    while True:
        try:
            choice = input(f"Enter number (1-{len(sub_list)}), or 0 to skip: ")
            choice_idx = int(choice) - 1
            if choice_idx == -1: return None
            if 0 <= choice_idx < len(sub_list): return sub_list[choice_idx]
            else: logging.warning("Invalid selection. Please try again.")
        except (ValueError, IndexError):
            logging.warning("Invalid input. Please enter a number.")

def _get_sub_from_query(lang: str, sub_type: str, args: argparse.Namespace, api_keys: dict) -> str | None:
    """Helper function for the analysis workflow to get a subtitle by query."""
    search_results = fetcher.search_subtitles_by_query(args.query, lang, api_keys['opensubtitles'])
    if not search_results: return None

    selected_meta = _prompt_for_selection(search_results, f"{sub_type} ({lang})")
    if not selected_meta: return None

    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".srt") as tmp:
        save_path = tmp.name

    return fetcher.download_subtitle(selected_meta, api_keys['opensubtitles'], save_path)

def _fetch_and_align_orig_sub(video_path: str, dub_sub_path: str, args: argparse.Namespace, api_keys: dict) -> str | None:
    """
    Implements the Sept 6th strategy: fetches an original language sub by title,
    then aligns it to the provided dub subtitle.
    """
    logging.info("--- Searching for original subtitle by title to align with local dub file. ---")

    # 1. Get query from filename
    query = re.sub(r'[.\[\]()]', ' ', os.path.splitext(os.path.basename(video_path))[0])
    query = ' '.join(query.split())
    logging.info(f"Generated search query: '{query}'")

    # 2. Search for the subtitle
    search_results = fetcher.search_subtitles_by_query(query, args.lang_orig, api_keys['opensubtitles'])
    if not search_results:
        logging.warning("No results found from title search.")
        return None

    # 3. Select the subtitle
    if args.interactive:
        selected_meta = _prompt_for_selection(search_results, f"original ({args.lang_orig})")
    else:
        selected_meta = max(search_results, key=lambda s: s.get("attributes", {}).get("download_count", 0))
        logging.info(f"Auto-selected original sub: {selected_meta.get('attributes', {}).get('release', 'N/A')} (Downloads: {selected_meta.get('attributes', {}).get('download_count', 0)})")

    if not selected_meta:
        logging.warning("No original subtitle selected from title search.")
        return None

    # 4. Download to a temporary file
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".srt") as tmp:
        unaligned_orig_path = tmp.name

    unaligned_orig_path = fetcher.download_subtitle(selected_meta, api_keys['opensubtitles'], unaligned_orig_path)
    if not unaligned_orig_path:
        logging.error("Failed to download selected subtitle.")
        return None

    # 5. Align it
    logging.info(f"Aligning '{os.path.basename(unaligned_orig_path)}' to '{os.path.basename(dub_sub_path)}'")
    master_subs = pysubs2.load(dub_sub_path)
    target_subs = pysubs2.load(unaligned_orig_path)
    aligned_subs = aligner.align_by_index(master_subs, target_subs)

    # 6. Save aligned version to another temp file
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".srt", encoding='utf-8') as tmp_aligned:
        aligned_subs.save(tmp_aligned.name)
        aligned_orig_path = tmp_aligned.name

    # 7. Clean up unaligned file
    os.remove(unaligned_orig_path)

    logging.info("Alignment successful.")
    return aligned_orig_path


def run_analysis_workflow(args: argparse.Namespace, api_keys: dict, styles: dict):
    """Runs the film analysis workflow based on title search and timing alignment."""
    logging.info(f"\n--- Starting Analysis Mode for query: '{args.query}' ---")

    # Use path as the output directory
    output_dir = os.path.abspath(args.path)
    os.makedirs(output_dir, exist_ok=True)
    logging.info(f"Output will be saved to: {output_dir}")

    try:
        # 1. Get Original Language Subtitle
        orig_sub_path = _get_sub_from_query(args.lang_orig, "original", args, api_keys)
        if not orig_sub_path:
            logging.error(f"Could not retrieve original language ({args.lang_orig}) subtitle. Aborting.")
            return

        # 2. Get Dub Language Subtitle
        dub_sub_path = _get_sub_from_query(args.lang_dub, "dub", args, api_keys)
        if not dub_sub_path:
            logging.error(f"Could not retrieve dub language ({args.lang_dub}) subtitle. Aborting.")
            return

        # 3. Align Timings
        logging.info("Loading subtitles for alignment...")
        master_subs = pysubs2.load(dub_sub_path)
        target_subs = pysubs2.load(orig_sub_path)
        aligned_orig_subs = aligner.align_by_index(master_subs, target_subs)

        # 4. Translate Dub Subtitle
        logging.info(f"Translating dub file: {os.path.basename(dub_sub_path)}")
        translated_texts = translator.translate_subtitle_file(filepath=dub_sub_path, target_lang=args.lang_native, api_key=api_keys['deepl'])
        if not translated_texts:
            logging.error(f"Could not translate subtitle file for query '{args.query}'. Skipping.")
            return

        # 5. Merge and Save
        output_filename = f"{args.query.replace(' ', '_')}.{args.lang_orig}-{args.lang_dub}.sublearn.ass"
        output_path = os.path.join(output_dir, output_filename)

        # We need to save the aligned subs to a temp file to pass its path to the merger
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".srt", encoding='utf-8') as tmp_aligned:
            aligned_orig_subs.save(tmp_aligned.name)
            aligned_orig_path = tmp_aligned.name

        merger.create_merged_subtitle_file(
            dub_sub_path=dub_sub_path,
            translated_texts=translated_texts,
            output_path=output_path,
            orig_sub_path=aligned_orig_path,
            styles=styles
        )
        logging.info(f"--- Successfully completed analysis for: '{args.query}' ---")

        # Clean up temporary files
        os.remove(orig_sub_path)
        os.remove(dub_sub_path)
        os.remove(aligned_orig_path)

    except Exception:
        logging.error(f"An unexpected error occurred during analysis for '{args.query}'.", exc_info=True)


def run_learn_workflow(args: argparse.Namespace, api_keys: dict, styles: dict, transcriber_settings: dict):
    """Runs the language learning workflow based on video files."""
    input_path = os.path.abspath(args.path)
    videos_to_process = []
    if os.path.isdir(input_path):
        if args.orig_file or args.dub_file:
            logging.error("--orig-file and --dub-file cannot be used with a directory path.")
            sys.exit(1)
        logging.info(f"Scanning directory for video files: {input_path}")
        supported_extensions = ['.mkv', '.mp4', '.avi', '.mov']
        videos_to_process = [os.path.join(input_path, f) for f in os.listdir(input_path) if os.path.isfile(os.path.join(input_path, f)) and os.path.splitext(f)[1].lower() in supported_extensions]
        logging.info(f"Found {len(videos_to_process)} video file(s) to process.")
    elif os.path.isfile(input_path):
        videos_to_process = [input_path]
    else:
        logging.error(f"The provided path is not a valid file or directory: {input_path}")
        sys.exit(1)

    for video_path in videos_to_process:
        process_video_file(video_path, args, api_keys, styles, transcriber_settings)


def process_video_file(video_path: str, args: argparse.Namespace, api_keys: dict, styles: dict, transcriber_settings: dict):
    """Processes a single video file for the 'learn' mode."""
    logging.info(f"\n--- Starting processing for: {os.path.basename(video_path)} ---")
    video_filename_no_ext = os.path.splitext(os.path.basename(video_path))[0]
    output_dir = os.path.join(os.path.dirname(video_path), video_filename_no_ext)
    os.makedirs(output_dir, exist_ok=True)
    logging.info(f"Output will be saved to: {output_dir}")

    try:
        orig_sub_path, dub_sub_path = None, None
        logging.info("--- Locating Subtitle Files ---")
        if args.orig_file and os.path.exists(args.orig_file): orig_sub_path = args.orig_file
        if args.dub_file and os.path.exists(args.dub_file): dub_sub_path = args.dub_file

        local_orig_path = os.path.join(output_dir, f"{video_filename_no_ext}.{args.lang_orig}.srt")
        if not orig_sub_path and os.path.exists(local_orig_path): orig_sub_path = local_orig_path
        local_dub_path = os.path.join(output_dir, f"{video_filename_no_ext}.{args.lang_dub}.srt")
        if not dub_sub_path and os.path.exists(local_dub_path): dub_sub_path = local_dub_path

        # New local-only alignment workflow
        if orig_sub_path and dub_sub_path and args.timing_master:
            logging.info(f"--- Running local-only alignment workflow. Master: {args.timing_master} ---")

            # 1. Translate the original dub file before any alignment happens to it.
            logging.info(f"Translating dub file: {os.path.basename(dub_sub_path)}")
            translated_texts = translator.translate_subtitle_file(filepath=dub_sub_path, target_lang=args.lang_native, api_key=api_keys['deepl'])
            if not translated_texts:
                logging.error(f"Could not translate subtitle file for {video_filename_no_ext}. Skipping.")
                return

            # 2. Perform the alignment
            if args.timing_master == 'orig':
                master_path, target_path = orig_sub_path, dub_sub_path
                log_msg = f"Aligning dub subtitle '{os.path.basename(target_path)}' to original '{os.path.basename(master_path)}'"
            else:  # 'dub'
                master_path, target_path = dub_sub_path, orig_sub_path
                log_msg = f"Aligning original subtitle '{os.path.basename(target_path)}' to dub '{os.path.basename(master_path)}'"

            logging.info(log_msg)
            master_subs = pysubs2.load(master_path)
            target_subs = pysubs2.load(target_path)
            aligned_target_subs = aligner.align_by_index(master_subs, target_subs)

            with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".srt", encoding='utf-8') as tmp_aligned:
                aligned_target_subs.save(tmp_aligned.name)
                aligned_path = tmp_aligned.name

            # 3. Set final paths for the merger
            if args.timing_master == 'orig':
                final_orig_path, final_dub_path = master_path, aligned_path
            else:  # 'dub'
                final_orig_path, final_dub_path = aligned_path, master_path

            # 4. Merge and exit this function for the current video file
            output_path = os.path.join(output_dir, f"{video_filename_no_ext}.sublearn.ass")
            merger.create_merged_subtitle_file(
                dub_sub_path=final_dub_path,
                translated_texts=translated_texts,
                output_path=output_path,
                orig_sub_path=final_orig_path,
                styles=styles
            )
            logging.info(f"--- Successfully completed processing for: {os.path.basename(video_path)} ---")
            return

        # Original workflow: if dub is provided, find and align original sub by title
        if dub_sub_path and not orig_sub_path and not args.no_orig_search:
            aligned_path = _fetch_and_align_orig_sub(video_path, dub_sub_path, args, api_keys)
            if aligned_path:
                orig_sub_path = aligned_path

        use_online_search = not args.force_transcriber and (not orig_sub_path or not dub_sub_path)
        if use_online_search:
            movie_hash = fetcher.get_movie_hash(video_path)
            if movie_hash:
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

        if not dub_sub_path and (args.fallback_to_transcriber or args.force_transcriber):
            logging.info("--- No suitable dub subtitle found online. Falling back to AI transcription. ---")
            dub_sub_path = transcriber.transcribe_audio_track(video_path=video_path, language_code=args.lang_dub, output_dir=output_dir, model_size=args.whisper_model, audio_track_index=args.audio_track)

        if not dub_sub_path:
            logging.error(f"Could not retrieve or generate a dub subtitle for {video_filename_no_ext}. Skipping.")
            return

        logging.info(f"Translating dub file: {os.path.basename(dub_sub_path)}")
        translated_texts = translator.translate_subtitle_file(filepath=dub_sub_path, target_lang=args.lang_native, api_key=api_keys['deepl'])
        if not translated_texts:
            logging.error(f"Could not translate subtitle file for {video_filename_no_ext}. Skipping.")
            return

        output_path = os.path.join(output_dir, f"{video_filename_no_ext}.sublearn.ass")
        merger.create_merged_subtitle_file(dub_sub_path=dub_sub_path, translated_texts=translated_texts, output_path=output_path, orig_sub_path=orig_sub_path, styles=styles)
        logging.info(f"--- Successfully completed processing for: {os.path.basename(video_path)} ---")
    except Exception:
        logging.error(f"An unexpected error occurred while processing {os.path.basename(video_path)}.", exc_info=True)

def load_styles_from_config(config: configparser.ConfigParser) -> dict:
    """Loads subtitle styles from the config parser, with defaults."""
    alignment_map = {"BOTTOM_LEFT": 1, "BOTTOM_CENTER": 2, "BOTTOM_RIGHT": 3, "MIDDLE_LEFT": 4, "MIDDLE_CENTER": 5, "MIDDLE_RIGHT": 6, "TOP_LEFT": 7, "TOP_CENTER": 8, "TOP_RIGHT": 9}
    styles = {'dub_fontsize': 24, 'dub_color': (255, 255, 0), 'dub_alignment': 8, 'dub_marginv': 10, 'trans_fontsize': 22, 'trans_color': (0, 255, 255), 'trans_alignment': 2, 'trans_marginv': 40, 'orig_fontsize': 14, 'orig_color': (255, 255, 255), 'orig_alignment': 5, 'orig_marginv': 10}
    if not config.has_section('STYLES'): return styles
    def get_style(key, getter, default):
        try: return getter('STYLES', key)
        except (configparser.NoOptionError, ValueError): return default
    styles['orig_fontsize'] = get_style('orig_fontsize', config.getint, styles['orig_fontsize'])
    styles['dub_fontsize'] = get_style('dub_fontsize', config.getint, styles['dub_fontsize'])
    styles['trans_fontsize'] = get_style('trans_fontsize', config.getint, styles['trans_fontsize'])
    styles['orig_marginv'] = get_style('orig_marginv', config.getint, styles['orig_marginv'])
    styles['dub_marginv'] = get_style('dub_marginv', config.getint, styles['dub_marginv'])
    styles['trans_marginv'] = get_style('trans_marginv', config.getint, styles['trans_marginv'])
    styles['orig_color'] = (get_style('orig_color_r', config.getint, 255), get_style('orig_color_g', config.getint, 255), get_style('orig_color_b', config.getint, 255))
    styles['dub_color'] = (get_style('dub_color_r', config.getint, 255), get_style('dub_color_g', config.getint, 255), get_style('dub_color_b', config.getint, 0))
    styles['trans_color'] = (get_style('trans_color_r', config.getint, 0), get_style('trans_color_g', config.getint, 255), get_style('trans_color_b', config.getint, 255))
    styles['orig_alignment'] = alignment_map.get(get_style('orig_alignment', config.get, 'TOP_CENTER').upper(), styles['orig_alignment'])
    styles['dub_alignment'] = alignment_map.get(get_style('dub_alignment', config.get, 'MIDDLE_CENTER').upper(), styles['dub_alignment'])
    styles['trans_alignment'] = alignment_map.get(get_style('trans_alignment', config.get, 'BOTTOM_CENTER').upper(), styles['trans_alignment'])
    return styles

def load_transcriber_settings(config: configparser.ConfigParser) -> dict:
    settings = {'model_size': 'base'}
    if not config.has_section('TRANSCRIBER'): return settings
    settings['model_size'] = config.get('TRANSCRIBER', 'model_size', fallback='base')
    return settings

def main():
    base_path = get_base_path()
    log_file_path = os.path.join(base_path, 'sublearn.log')
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename=log_file_path, filemode='w')
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(message)s'))
    logging.getLogger().addHandler(console_handler)

    config = configparser.ConfigParser()
    config_path = os.path.join(base_path, 'config.ini')
    if not os.path.exists(config_path):
        logging.error(f"Configuration file '{config_path}' not found. Please create it from the example.")
        sys.exit(1)
    config.read(config_path)
    try:
        api_keys = {'opensubtitles': config.get('API_KEYS', 'OPENSUBTITLES_API_KEY'), 'deepl': config.get('API_KEYS', 'DEEPL_API_KEY')}
        if 'YOUR_API_KEY_HERE' in api_keys.values(): logging.warning("API key in 'config.ini' still has the default placeholder value.")
    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        logging.error(f"Error reading API keys from '{config_path}': {e}", exc_info=True)
        sys.exit(1)

    styles = load_styles_from_config(config)
    transcriber_settings = load_transcriber_settings(config)

    parser = argparse.ArgumentParser(description="SubLearn: A tool for creating multi-track subtitles for language learning and film analysis.")
    parser.add_argument("path", help="Path to a local video file/directory (learn mode) or an output directory (analysis mode).")
    parser.add_argument("--lang_dub", required=True, help="The language of the dubbed audio track (e.g., 'hu', 'es').")
    parser.add_argument("--lang_orig", default="en", help="The original language of the video (e.g., 'en').")
    parser.add_argument("--lang_native", default="EN-US", help="Your native language for translation (e.g., 'EN-US', 'DE').")

    # Mode selection
    parser.add_argument("--mode", default="learn", choices=['learn', 'analyze'], help="Set the tool's mode of operation.")

    # Learn Mode arguments
    learn_group = parser.add_argument_group('Learn Mode', 'Arguments for the language learning workflow (default mode)')
    learn_group.add_argument("--interactive", action="store_true", help="Enable interactive mode to manually select subtitles.")
    learn_group.add_argument("--no-orig-search", action="store_true", help="Do not search for an original language subtitle online.")
    learn_group.add_argument("--orig-file", help="Path to a local .srt file for the original language track.")
    learn_group.add_argument("--dub-file", help="Path to a local .srt file for the dub track.")
    learn_group.add_argument("--timing-master", choices=['orig', 'dub'], help="When using two local SRT files, specify which one is the timing master ('orig' or 'dub').")
    learn_group.add_argument("--force-transcriber", action="store_true", help="Skip online search and transcribe the audio directly.")
    learn_group.add_argument("--fallback-to-transcriber", action="store_true", help="Transcribe if a dub subtitle is not found online.")
    learn_group.add_argument("--audio-track", type=int, default=0, help="The index of the audio track to transcribe (default: 0).")
    learn_group.add_argument("--whisper-model", default=transcriber_settings['model_size'], help=f"The Whisper model to use for transcription (default: {transcriber_settings['model_size']}).")

    # Analysis Mode arguments
    analysis_group = parser.add_argument_group('Analysis Mode', 'Arguments for the film analysis workflow')
    analysis_group.add_argument("--query", help="The movie title to search for online. Required for analysis mode.")

    args = parser.parse_args()

    if args.mode == 'analyze':
        if not args.query:
            args.query = input("Please enter the movie title to search for: ")
        run_analysis_workflow(args, api_keys, styles)
    else: # mode == 'learn'
        run_learn_workflow(args, api_keys, styles, transcriber_settings)

if __name__ == "__main__":
    main()
