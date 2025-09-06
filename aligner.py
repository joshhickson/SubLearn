import pysubs2
import logging
import copy

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
