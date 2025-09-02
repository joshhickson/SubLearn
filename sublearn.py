import argparse
import os
import fetcher
import translator
import merger

# --- Configuration ---
# In Phase 1, API keys are hardcoded.
# In Phase 2, these will be moved to a configuration file.
OPENSUBTITLES_API_KEY = "CBTYAdSw5p7cE2kyRta9QMJruZ0DcAnV"
DEEPL_API_KEY = "f6f6ae27-a52d-45e3-b7e6-91717c251c04:fx"

def main():
    """
    Main function to run the SubLearn command-line interface.
    """
    parser = argparse.ArgumentParser(
        description="SubLearn: A tool for creating multi-track subtitles for language learning."
    )
    parser.add_argument("video_path", help="The full path to the local video file.")
    parser.add_argument("--lang_orig", default="en", help="The original language of the video (e.g., 'en').")
    parser.add_argument("--lang_dub", required=True, help="The language of the dubbed audio track (e.g., 'hu', 'es').")
    parser.add_argument("--lang_native", default="EN-US", help="Your native language for translation (e.g., 'EN-US', 'DE').")
    parser.add_argument("--dub-file", help="Path to a local .srt file to use for the dub track, skipping the online search.")
    parser.add_argument("--no-orig-search", action="store_true", help="When using --dub-file, do not search for an original language subtitle online.")

    args = parser.parse_args()

    print("--- Starting SubLearn Workflow ---")

    temp_files_to_clean = []
    orig_sub_path = None
    dub_sub_path = None

    try:
        if args.dub_file:
            # --- Workflow Path 2: User provides the dub subtitle file ---
            print(f"Using local file for dub track: {args.dub_file}")
            if not os.path.exists(args.dub_file):
                print(f"Error: The file specified via --dub-file does not exist: {args.dub_file}")
                return

            dub_sub_path = args.dub_file

            # If --no-orig-search is specified, skip the online search for the original subtitle.
            if args.no_orig_search:
                print("Skipping online search for original subtitle as requested.")
                orig_sub_path = None
            else:
                # Fetch only the original language subtitle
                print("Searching online for the original language subtitle...")
                orig_sub_path_temp, _ = fetcher.find_and_download_subtitles(
                    video_path=args.video_path,
                    lang_orig=args.lang_orig,
                    lang_dub=args.lang_dub, # Still needed for API consistency, but won't be used for search
                    api_key=OPENSUBTITLES_API_KEY,
                    skip_dub=True
                )
                if orig_sub_path_temp:
                    orig_sub_path = orig_sub_path_temp
                    temp_files_to_clean.append(orig_sub_path)

        else:
            # --- Workflow Path 1: Default behavior, search for both subtitles ---
            print("Searching online for both original and dub language subtitles...")
            orig_sub_path_temp, dub_sub_path_temp = fetcher.find_and_download_subtitles(
                video_path=args.video_path,
                lang_orig=args.lang_orig,
                lang_dub=args.lang_dub,
                api_key=OPENSUBTITLES_API_KEY,
                skip_dub=False
            )
            if orig_sub_path_temp:
                orig_sub_path = orig_sub_path_temp
                temp_files_to_clean.append(orig_sub_path)
            if dub_sub_path_temp:
                dub_sub_path = dub_sub_path_temp
                temp_files_to_clean.append(dub_sub_path)

        # --- Main processing continues here ---
        if not dub_sub_path:
            print("Could not retrieve the dub subtitle file. Exiting.")
            return

        # 2. Translate the dub subtitle file
        translated_texts = translator.translate_subtitle_file(
            filepath=dub_sub_path,
            target_lang=args.lang_native,
            api_key=DEEPL_API_KEY
        )

        if translated_texts is None:
            print("Could not translate subtitle file. Exiting.")
            return

        # 3. Merge the three subtitle tracks into a final .ass file
        video_dir = os.path.dirname(args.video_path)
        video_filename = os.path.splitext(os.path.basename(args.video_path))[0]
        output_path = os.path.join(video_dir, f"{video_filename}.sublearn.ass")

        merger.create_merged_subtitle_file(
            dub_sub_path=dub_sub_path,
            translated_texts=translated_texts,
            output_path=output_path,
            orig_sub_path=orig_sub_path
        )

        print("\n--- SubLearn Workflow Complete ---")
        print(f"Final subtitle file saved to: {output_path}")

    except Exception as e:
        print(f"\nAn unexpected error occurred during the workflow: {e}")
    finally:
        # 4. Clean up ONLY the temporary files downloaded by the script
        if temp_files_to_clean:
            print("Cleaning up temporary files...")
            for f_path in temp_files_to_clean:
                if os.path.exists(f_path):
                    os.remove(f_path)
            print("Cleanup complete.")


if __name__ == "__main__":
    main()
