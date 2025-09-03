import argparse
import os
import fetcher
import translator
import merger
import configparser
import sys

def main():
    """
    Main function to run the SubLearn command-line interface.
    """
    # --- Configuration Loading ---
    config = configparser.ConfigParser()
    config_path = 'config.ini'

    if not os.path.exists(config_path):
        print(f"Error: Configuration file '{config_path}' not found.")
        print("Please create it by copying 'config.ini.example' and filling in your API keys.")
        sys.exit(1)

    config.read(config_path)

    try:
        OPENSUBTITLES_API_KEY = config.get('API_KEYS', 'OPENSUBTITLES_API_KEY')
        DEEPL_API_KEY = config.get('API_KEYS', 'DEEPL_API_KEY')
        if 'YOUR_API_KEY_HERE' in [OPENSUBTITLES_API_KEY, DEEPL_API_KEY]:
            print("Warning: API key in 'config.ini' still has the default placeholder value.")
    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        print(f"Error reading API keys from '{config_path}': {e}")
        print("Please ensure 'config.ini' has the [API_KEYS] section with OPENSUBTITLES_API_KEY and DEEPL_API_KEY.")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="SubLearn: A tool for creating multi-track subtitles for language learning."
    )
    parser.add_argument("video_path", help="The full path to the local video file.")
    parser.add_argument("--lang_orig", default="en", help="The original language of the video (e.g., 'en').")
    parser.add_argument("--lang_dub", required=True, help="The language of the dubbed audio track (e.g., 'hu', 'es').")
    parser.add_argument("--lang_native", default="EN-US", help="Your native language for translation (e.g., 'EN-US', 'DE').")
    parser.add_argument("--orig-file", help="Path to a local .srt file to use for the original language track, skipping the online search.")
    parser.add_argument("--dub-file", help="Path to a local .srt file to use for the dub track, skipping the online search.")
    parser.add_argument("--no-orig-search", action="store_true", help="When using --dub-file, do not search for an original language subtitle online.")

    args = parser.parse_args()

    # --- Create output directory based on video name ---
    video_filename_no_ext = os.path.splitext(os.path.basename(args.video_path))[0]
    output_dir = os.path.join(os.path.dirname(args.video_path), video_filename_no_ext)
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output will be saved to: {output_dir}")

    print("--- Starting SubLearn Workflow ---")

    orig_sub_path = None
    dub_sub_path = None

    try:
        # --- Subtitle Sourcing Workflow ---
        print("--- Locating Subtitle Files ---")

        # 1. Check for user-provided files via arguments
        if args.orig_file:
            if os.path.exists(args.orig_file):
                print(f"Using user-provided original subtitle: {args.orig_file}")
                orig_sub_path = args.orig_file
            else:
                print(f"Warning: File specified by --orig-file not found: {args.orig_file}")

        if args.dub_file:
            if os.path.exists(args.dub_file):
                print(f"Using user-provided dub subtitle: {args.dub_file}")
                dub_sub_path = args.dub_file
            else:
                print(f"Warning: File specified by --dub-file not found: {args.dub_file}")

        # 2. Check for local files in the output directory (auto-detection)
        if not orig_sub_path:
            local_orig_path = os.path.join(output_dir, f"{video_filename_no_ext}.{args.lang_orig}.srt")
            if os.path.exists(local_orig_path):
                print(f"Found local original subtitle: {local_orig_path}")
                orig_sub_path = local_orig_path

        if not dub_sub_path:
            local_dub_path = os.path.join(output_dir, f"{video_filename_no_ext}.{args.lang_dub}.srt")
            if os.path.exists(local_dub_path):
                print(f"Found local dub subtitle: {local_dub_path}")
                dub_sub_path = local_dub_path

        # 3. Fetch missing subtitles from online
        # If a file is not found locally, search for it online unless specified not to.
        should_skip_orig_search = (orig_sub_path is not None) or args.no_orig_search
        should_skip_dub_search = (dub_sub_path is not None)

        if not should_skip_orig_search or not should_skip_dub_search:
            fetched_orig, fetched_dub = fetcher.find_and_download_subtitles(
                video_path=args.video_path,
                lang_orig=args.lang_orig,
                lang_dub=args.lang_dub,
                api_key=OPENSUBTITLES_API_KEY,
                skip_orig=should_skip_orig_search,
                skip_dub=should_skip_dub_search,
                output_dir=output_dir
            )
            if fetched_orig:
                orig_sub_path = fetched_orig
            if fetched_dub:
                dub_sub_path = fetched_dub

        # --- Main Processing ---
        print("\n--- Starting Main Processing ---")
        if not dub_sub_path:
            print("Error: Could not retrieve the dub subtitle file. A dub file is required to proceed. Exiting.")
            return

        # 2. Translate the dub subtitle file
        print(f"Translating dub file: {dub_sub_path}")
        translated_texts = translator.translate_subtitle_file(
            filepath=dub_sub_path,
            target_lang=args.lang_native,
            api_key=DEEPL_API_KEY
        )

        if translated_texts is None:
            print("Error: Could not translate subtitle file. Exiting.")
            return

        # 3. Merge the subtitle tracks into a final .ass file
        output_path = os.path.join(output_dir, f"{video_filename_no_ext}.sublearn.ass")
        print(f"Creating merged subtitle file at: {output_path}")

        merger.create_merged_subtitle_file(
            dub_sub_path=dub_sub_path,
            translated_texts=translated_texts,
            output_path=output_path,
            orig_sub_path=orig_sub_path  # This can be None, and the merger will handle it
        )

        print("\n--- SubLearn Workflow Complete ---")
        print(f"Final subtitle file saved to: {output_path}")

    except Exception as e:
        print(f"\nAn unexpected error occurred during the workflow: {e}")



if __name__ == "__main__":
    main()
