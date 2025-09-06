import pytest
import pysubs2
import sys
import os

# Add the root directory to the Python path to allow importing modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import aligner

@pytest.fixture
def subtitle_pair():
    """Provides a pair of pysubs2.SSAFile objects for testing."""
    master_text = (
        "1\n00:00:01,000 --> 00:00:02,000\nMaster Line 1\n\n"
        "2\n00:00:03,000 --> 00:00:04,000\nMaster Line 2\n\n"
    )
    target_text = (
        "1\n00:01:01,000 --> 00:01:02,000\nTarget Line 1\n\n"
        "2\n00:01:03,000 --> 00:01:04,000\nTarget Line 2\n\n"
        "3\n00:01:05,000 --> 00:01:06,000\nTarget Line 3\n\n"
    )
    master_subs = pysubs2.SSAFile.from_string(master_text)
    target_subs = pysubs2.SSAFile.from_string(target_text)
    return master_subs, target_subs

def test_align_by_index_happy_path(subtitle_pair):
    """Tests alignment when master and target have the same (truncated) length."""
    master, target = subtitle_pair
    # Truncate target to match master length for this test
    target.events = target.events[:2]

    aligned = aligner.align_by_index(master, target)

    assert len(aligned) == 2
    # Check first line
    assert aligned[0].start == master[0].start  # 1000 ms
    assert aligned[0].end == master[0].end      # 2000 ms
    assert aligned[0].text == "Target Line 1"
    # Check second line
    assert aligned[1].start == master[1].start  # 3000 ms
    assert aligned[1].end == master[1].end      # 4000 ms
    assert aligned[1].text == "Target Line 2"

def test_align_by_index_different_lengths(subtitle_pair):
    """Tests that alignment truncates to the shorter length."""
    master, target = subtitle_pair # master has 2 lines, target has 3

    # --- Case 1: Master is shorter ---
    aligned_master_shorter = aligner.align_by_index(master, target)
    assert len(aligned_master_shorter) == 2
    assert aligned_master_shorter[0].start == 1000
    assert aligned_master_shorter[1].start == 3000

    # --- Case 2: Target is shorter ---
    master.events = master.events * 2 # master now has 4 lines
    aligned_target_shorter = aligner.align_by_index(master, target)
    assert len(aligned_target_shorter) == 3 # Target length is 3
    assert aligned_target_shorter[0].start == 1000
    assert aligned_target_shorter[2].start == master[2].start # Should match the 3rd line of the new master

def test_align_by_index_empty_files():
    """Tests that the function handles empty subtitle files gracefully."""
    empty_subs = pysubs2.SSAFile()
    non_empty_subs = pysubs2.SSAFile.from_string("1\n00:00:01,000 --> 00:00:02,000\nLine 1\n\n")

    # Both empty
    aligned1 = aligner.align_by_index(empty_subs, empty_subs)
    assert len(aligned1) == 0

    # Master empty
    aligned2 = aligner.align_by_index(empty_subs, non_empty_subs)
    assert len(aligned2) == 0

    # Target empty
    aligned3 = aligner.align_by_index(non_empty_subs, empty_subs)
    assert len(aligned3) == 0
