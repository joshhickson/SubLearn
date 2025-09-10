import pysubs2
import logging
import copy
from thefuzz import process

def align_by_content(master_subs: pysubs2.SSAFile, target_subs: pysubs2.SSAFile, bridge_subs: pysubs2.SSAFile) -> pysubs2.SSAFile:
    """
    Aligns the timing of a target subtitle file to a master subtitle file by matching content.

    This function uses a "bridge" subtitle file (typically a translation of the master)
    to find the best content match for each line in the target file. It then applies the
    corresponding timestamp from the master file. This is more robust than index-based
    alignment when line counts or structures differ.

    Args:
        master_subs: The subtitle file with the correct reference timings (e.g., dub).
        target_subs: The subtitle file to be retimed (e.g., original language).
        bridge_subs: The subtitle file to use for content matching (e.g., a translation of the dub).

    Returns:
        A new SSAFile object with the timings of target_subs adjusted based on content.
    """
    logging.info("Aligning subtitle timings by content matching...")
    aligned_subs = copy.deepcopy(target_subs)

    bridge_texts = [event.text for event in bridge_subs]

    if not bridge_texts:
        logging.error("Bridge subtitle file has no content to match against. Aborting alignment.")
        return target_subs # Return original subs

    total_events = len(aligned_subs)
    matched_count = 0

    for i, target_event in enumerate(aligned_subs.events):
        # Find the best match for the target text in the bridge texts
        # We use a score cutoff to avoid matching completely unrelated lines.
        result = process.extractOne(target_event.text, bridge_texts, score_cutoff=75)

        if result:
            best_match, score = result
            try:
                # Find the index of the best match in the original list.
                index = bridge_texts.index(best_match)

                # Apply the timing from the master subtitle at that index
                master_event = master_subs.events[index]
                target_event.start = master_event.start
                target_event.end = master_event.end
                matched_count += 1

                # To prevent a single bridge line from being matched multiple times,
                # we replace it with a unique, unlikely string.
                bridge_texts[index] = f"__MATCHED_{i}__"
            except ValueError:
                # This should not happen if the match was found, but as a safeguard:
                logging.warning(f"Match '{best_match}' not found in bridge text list. This is unexpected.")
        else:
            logging.warning(f"No good match found for line {i+1}: '{target_event.text}'. Keeping original timing.")

    logging.info(f"Content alignment complete. {matched_count}/{total_events} events were successfully retimed.")
    return aligned_subs

def align_by_index(master_subs: pysubs2.SSAFile, target_subs: pysubs2.SSAFile) -> pysubs2.SSAFile:
    """
    Aligns the timing of a target subtitle file to a master subtitle file.

    This function works by iterating through both files and applying the start
    and end times from each event in the master file to the event at the
    same index in the target file.

    Args:
        master_subs: The subtitle file to use as the timing reference.
        target_subs: The subtitle file whose timings will be modified.

    Returns:
        A new SSAFile object with the timings of target_subs adjusted.
    """
    logging.info("Aligning subtitle timings by index...")

    # Make a deep copy to avoid modifying the original object
    aligned_subs = copy.deepcopy(target_subs)

    master_len = len(master_subs)
    target_len = len(aligned_subs)

    if master_len != target_len:
        logging.warning(
            f"Subtitle files have different line counts ({master_len} vs {target_len}). "
            f"Alignment will be truncated to the shorter length."
        )

    min_len = min(master_len, target_len)

    # Truncate the events list to the shortest length
    aligned_subs.events = aligned_subs.events[:min_len]

    # Apply timing from master to the new copy
    for i in range(min_len):
        aligned_subs.events[i].start = master_subs.events[i].start
        aligned_subs.events[i].end = master_subs.events[i].end

    logging.info(f"Alignment complete. {min_len} subtitle events were aligned.")
    return aligned_subs
