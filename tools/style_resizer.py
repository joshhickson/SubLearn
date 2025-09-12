import argparse
import os
import sys
import pysubs2

"""
ASS Subtitle Style Resizer

This script allows you to change the font size for the specific tracks
(Original, Dub, and Translation) within a SubLearn-generated .ass file.

Usage:
    python tools/style_resizer.py --ass-file <path_to_ass> [options]

Example:
    python tools/style_resizer.py --ass-file "The.Matrix.1999.sublearn.09.10.2025.ass" --orig-size 16 --dub-size 28

Arguments:
    --ass-file (required): The path to the .ass subtitle file to modify.
    --orig-size (optional): The new font size for the 'Style_Orig' track.
    --dub-size (optional): The new font size for the 'Style_Dub' track.
    --trans-size (optional): The new font size for the 'Style_Trans' track.
"""

def main():
    parser = argparse.ArgumentParser(
        description="Resizes font styles in a SubLearn .ass file."
    )
    parser.add_argument("--ass-file", required=True, help="Path to the .ass subtitle file.")
    parser.add_argument("--orig-size", type=int, help="New font size for the Original track.")
    parser.add_argument("--dub-size", type=int, help="New font size for the Dub track.")
    parser.add_argument("--trans-size", type=int, help="New font size for the Translation track.")

    args = parser.parse_args()

    if not os.path.exists(args.ass_file):
        print(f"Error: File not found at {args.ass_file}", file=sys.stderr)
        sys.exit(1)

    try:
        print(f"Loading subtitle file: {args.ass_file}")
        subs = pysubs2.load(args.ass_file, encoding="utf-8")
        print("File loaded successfully.")
    except Exception as e:
        print(f"Error loading subtitle file: {e}", file=sys.stderr)
        sys.exit(1)

    styles_to_update = {
        'Style_Orig': args.orig_size,
        'Style_Dub': args.dub_size,
        'Style_Trans': args.trans_size
    }

    updated = False
    for style_name, new_size in styles_to_update.items():
        if new_size is not None:
            if style_name in subs.styles:
                old_size = subs.styles[style_name].fontsize
                subs.styles[style_name].fontsize = float(new_size)
                print(f"Updated {style_name}: Fontsize changed from {old_size} to {new_size}")
                updated = True
            else:
                print(f"Warning: Style '{style_name}' not found in the file. Skipping.", file=sys.stderr)

    if updated:
        try:
            subs.save(args.ass_file)
            print(f"\nSuccessfully saved updated styles to {args.ass_file}")
        except Exception as e:
            print(f"Error saving file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("\nNo font sizes were specified, so no changes were made.")

if __name__ == "__main__":
    main()
