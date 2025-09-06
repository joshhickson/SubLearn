import pysubs2
import copy
import logging

def create_merged_subtitle_file(
    dub_sub_path: str,
    translated_texts: list[str],
    output_path: str,
    styles: dict,
    orig_sub_path: str | None = None
):
    """
    Merges up to three subtitle tracks into a single, styled .ass file.
    """
    logging.info(f"Merging subtitles into {output_path}...")

    try:
        subs_dub = pysubs2.load(dub_sub_path, encoding="utf-8")
        subs_orig = None
        if orig_sub_path:
            try:
                subs_orig = pysubs2.load(orig_sub_path, encoding="utf-8")
            except FileNotFoundError:
                logging.warning(f"Original subtitle file not found at {orig_sub_path}. Proceeding without it.")

        if len(subs_dub) != len(translated_texts):
            logging.warning("Mismatch between number of dub lines and translated lines. Truncating.")
            min_len = min(len(subs_dub), len(translated_texts))
            subs_dub.events = subs_dub.events[:min_len]
            translated_texts = translated_texts[:min_len]

        subs_trans = copy.deepcopy(subs_dub)
        for i, line in enumerate(subs_trans):
            line.text = translated_texts[i]

        subs_final = pysubs2.SSAFile()

        # Define styles from the provided dictionary
        style_orig = pysubs2.SSAStyle(
            fontname="Arial", fontsize=styles['orig_fontsize'],
            primarycolor=pysubs2.Color(*styles['orig_color']),
            outlinecolor=pysubs2.Color(0, 0, 0), borderstyle=1, outline=1, shadow=0.5,
            alignment=styles['orig_alignment'], marginv=styles['orig_marginv']
        )
        style_dub = pysubs2.SSAStyle(
            fontname="Arial", fontsize=styles['dub_fontsize'],
            primarycolor=pysubs2.Color(*styles['dub_color']),
            outlinecolor=pysubs2.Color(0, 0, 0), borderstyle=1, outline=1, shadow=0.5,
            alignment=styles['dub_alignment'], marginv=styles['dub_marginv']
        )
        style_trans = pysubs2.SSAStyle(
            fontname="Arial", fontsize=styles['trans_fontsize'],
            primarycolor=pysubs2.Color(*styles['trans_color']),
            outlinecolor=pysubs2.Color(0, 0, 0), borderstyle=1, outline=1, shadow=0.5,
            alignment=styles['trans_alignment'], marginv=styles['trans_marginv']
        )

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
