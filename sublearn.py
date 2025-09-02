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

    args = parser.parse_args()

    print("--- Starting SubLearn Workflow ---")

    orig_sub_path = None
    dub_sub_path = None

    try:
        # 1. Fetch subtitles
        orig_sub_path, dub_sub_path = fetcher.find_and_download_subtitles(
            video_path=args.video_path,
            lang_orig=args.lang_orig,
            lang_dub=args.lang_dub,
            api_key=OPENSUBTITLES_API_KEY
        )

        if not orig_sub_path or not dub_sub_path:
            print("Could not retrieve subtitle files. Exiting.")
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
            orig_sub_path=orig_sub_path,
            dub_sub_path=dub_sub_path,
            translated_texts=translated_texts,
            output_path=output_path
        )

        print("\n--- SubLearn Workflow Complete ---")
        print(f"Final subtitle file saved to: {output_path}")

    except Exception as e:
        print(f"\nAn unexpected error occurred during the workflow: {e}")
    finally:
        # 4. Clean up temporary files
        print("Cleaning up temporary files...")
        if orig_sub_path and os.path.exists(orig_sub_path):
            os.remove(orig_sub_path)
        if dub_sub_path and os.path.exists(dub_sub_path):
            os.remove(dub_sub_path)
        print("Cleanup complete.")


if __name__ == "__main__":
    main()
