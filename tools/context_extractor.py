import argparse
import os
import sys
import pysubs2
from pysubs2 import time

"""
Context Extractor for Film Analysis

This script is a standalone tool designed to assist in film studies research by
extracting contextual information from a subtitle file and preparing a detailed
research prompt for a large language model like Google's Gemini.

Usage:
    python tools/context_extractor.py --srt-file <path_to_srt> --line-number <line_num>

Arguments:
    --srt-file: The path to the .srt subtitle file you want to analyze.
    --line-number: The specific line number in the SRT file that you want to
                   get context for.

The script will:
1.  Load the specified SRT file.
2.  Extract the dialogue from the target line number and the two lines
    immediately before and after it to create a contextual snippet.
3.  Generate a detailed, structured prompt that can be submitted to a large
    language model to get information about the scene's production, trivia,
    thematic significance, and director's intent.
4.  Use the `request_user_input` tool to present this prompt to the user.
5.  Receive the output from the user and display it in a formatted way.
"""

def main():
    parser = argparse.ArgumentParser(
        description="Extracts context from a specific line in an SRT file and prepares a research prompt."
    )
    parser.add_argument("--srt-file", required=True, help="Path to the .srt subtitle file.")
    parser.add_argument("--line-number", required=True, type=int, help="The line number to analyze.")
    parser.add_argument("--movie-title", required=True, help="The title of the movie (e.g., 'The Matrix (1999)').")

    args = parser.parse_args()

    if not os.path.exists(args.srt_file):
        print(f"Error: File not found at {args.srt_file}", file=sys.stderr)
        sys.exit(1)

    try:
        subs = pysubs2.load(args.srt_file, encoding="utf-8")
    except Exception as e:
        print(f"Error loading subtitle file: {e}", file=sys.stderr)
        sys.exit(1)

    if not (0 < args.line_number <= len(subs)):
        print(f"Error: Line number {args.line_number} is out of range. The file has {len(subs)} lines.", file=sys.stderr)
        sys.exit(1)

    # --- Context Extraction and Research Prompt Generation ---
    print(f"Successfully loaded {args.srt_file}.")
    print(f"Analyzing line number: {args.line_number}\n")

    # 1. Extract context (target line +/- 2 lines)
    start_index = max(0, args.line_number - 3)
    end_index = min(len(subs), args.line_number + 2)

    contextual_snippet = ""
    for i in range(start_index, end_index):
        line = subs[i]
        start_t = time.ms_to_str(line.start)
        end_t = time.ms_to_str(line.end)
        timestamp = f"{start_t} --> {end_t}"
        # Highlight the target line for clarity in the prompt
        if (i + 1) == args.line_number:
            contextual_snippet += f"--> LINE {i+1} ({timestamp}): {line.text}\n"
        else:
            contextual_snippet += f"    LINE {i+1} ({timestamp}): {line.text}\n"

    # 2. Formulate the research prompt for the user to pass to Gemini
    gemini_prompt = f"""**Film Studies Research Prompt**

**Movie:** {args.movie_title}
**Scene of Interest:** The following dialogue exchange:

---
**Contextual Subtitle Snippet:**
{contextual_snippet}
---

**Research Request:**
Please provide a detailed analysis of this scene. I am looking for the following specific information:

1.  **Production Details:** Are there any interesting behind-the-scenes facts about how this specific scene was filmed? (e.g., special effects techniques, actor experiences, set design choices, directorial challenges).

2.  **Trivia & Easter Eggs:** Are there any subtle details, references, or "easter eggs" hidden in this scene that a casual viewer might miss?

3.  **Thematic Analysis:** What is the significance of this scene in relation to the film's major themes (e.g., reality vs. illusion, fate vs. free will, control, transhumanism)? How does the dialogue and action in this scene contribute to the overall narrative and philosophical questions of the movie?

4.  **Director's Intent:** Is there any available information from interviews, director's commentaries, or other sources about the Wachowskis' intent or the specific meaning behind this scene?

Please provide a comprehensive but concise summary for each point.
"""

    # 3. Print the prompt for the user to copy.
    print("--- Please copy the following prompt and submit it to a language model ---")
    print(gemini_prompt)
    print("--------------------------------------------------------------------------\n")

    # 4. Wait for the user to paste the research from the LLM.
    print("After obtaining the research, paste it here, then press")
    print("Ctrl+D (Linux/macOS) or Ctrl+Z+Enter (Windows) to submit.")
    research_notes = sys.stdin.read()

    # 5. Format and display the final research notes.
    print("\n\n===============================================")
    print("      X-RAY ANALYSIS FOR YOUR SCENE")
    print("===============================================")
    print(f"\nBased on the dialogue from '{args.movie_title}', here is the analysis:\n")
    print(research_notes)
    print("\n===============================================\n")


if __name__ == "__main__":
    main()
