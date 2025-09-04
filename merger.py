import pysubs2
import copy
import logging

def create_merged_subtitle_file(
    dub_sub_path: str,
    translated_texts: list[str],
    output_path: str,
    orig_sub_path: str | None = None
):
    """
    Merges up to three subtitle tracks (original, dub, translated) into a single,
    styled Advanced SubStation Alpha (.ass) file.

    Args:
        dub_sub_path: Path to the dub language .srt file.
        translated_texts: A list of strings containing the translated dub text.
        output_path: The path to save the final .ass file.
        orig_sub_path: (Optional) Path to the original language .srt file.
    """
    logging.info(f"Merging subtitles into {output_path}...")

    try:
        # 1. Load source subtitle files
        subs_dub = pysubs2.load(dub_sub_path, encoding="utf-8")
        subs_orig = None
        if orig_sub_path:
            try:
                subs_orig = pysubs2.load(orig_sub_path, encoding="utf-8")
            except FileNotFoundError:
                logging.warning(f"Original subtitle file not found at {orig_sub_path}. Proceeding without it.")

        # 2. Create the translated subtitle object
        if len(subs_dub) != len(translated_texts):
            logging.warning("Mismatch between number of dub lines and translated lines. Truncating to shorter length.")
            min_len = min(len(subs_dub), len(translated_texts))
            subs_dub.events = subs_dub.events[:min_len]
            translated_texts = translated_texts[:min_len]

        subs_trans = copy.deepcopy(subs_dub)
        for i, line in enumerate(subs_trans):
            line.text = translated_texts[i]

        # 3. Initialize final output object
        subs_final = pysubs2.SSAFile()

        # 4. Define custom styles
        style_orig = pysubs2.SSAStyle(fontname="Arial", fontsize=20, primarycolor=pysubs2.Color(255, 255, 255), outlinecolor=pysubs2.Color(0, 0, 0), borderstyle=1, outline=1, shadow=0.5, alignment=pysubs2.Alignment.TOP_CENTER, marginv=10)
        style_dub = pysubs2.SSAStyle(fontname="Arial", fontsize=24, primarycolor=pysubs2.Color(255, 255, 0), outlinecolor=pysubs2.Color(0, 0, 0), borderstyle=1, outline=1, shadow=0.5, alignment=pysubs2.Alignment.MIDDLE_CENTER, marginv=10)
        style_trans = pysubs2.SSAStyle(fontname="Arial", fontsize=22, primarycolor=pysubs2.Color(0, 255, 255), outlinecolor=pysubs2.Color(0, 0, 0), borderstyle=1, outline=1, shadow=0.5, alignment=pysubs2.Alignment.BOTTOM_CENTER, marginv=10)

        subs_final.styles["Style_Dub"] = style_dub
        subs_final.styles["Style_Trans"] = style_trans
        if subs_orig:
            subs_final.styles["Style_Orig"] = style_orig

        # 5. Merge events and apply styles
        if subs_orig:
            for line in subs_orig:
                line.style = "Style_Orig"
                subs_final.append(line)

        for line in subs_dub:
            line.style = "Style_Dub"
            subs_final.append(line)

        for line in subs_trans:
            line.style = "Style_Trans"
            subs_final.append(line)

        # 6. Save the final merged and styled file
        subs_final.save(output_path)
        logging.info("Successfully created merged subtitle file.")

    except FileNotFoundError as e:
        logging.error(f"Subtitle file not found during merge: {e}", exc_info=True)
    except Exception as e:
        logging.error(f"An unexpected error occurred during merging: {e}", exc_info=True)
