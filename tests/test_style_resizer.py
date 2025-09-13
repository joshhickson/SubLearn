import pytest
import os
import sys
import subprocess
import pysubs2

# Add the root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

DUMMY_ASS_CONTENT = """
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Style_Orig,Arial,14,&H00FFFFFF,0,0,0,0,0,0,0,100,100,0,0,1,1,0.5,5,10,10,10,1
Style: Style_Dub,Arial,24,&H0000FFFF,0,0,0,0,0,0,0,100,100,0,0,1,1,0.5,8,10,10,10,1
Style: Style_Trans,Arial,22,&H00FFFF00,0,0,0,0,0,0,0,100,100,0,0,1,1,0.5,2,10,10,40,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:01.00,0:00:02.00,Style_Orig,,0,0,0,,Original Text
Dialogue: 0,0:00:01.00,0:00:02.00,Style_Dub,,0,0,0,,Dub Text
Dialogue: 0,0:00:01.00,0:00:02.00,Style_Trans,,0,0,0,,Translated Text
"""

@pytest.fixture
def setup_test_ass_file(tmp_path):
    """Creates a temporary .ass file for testing."""
    ass_path = tmp_path / "test.ass"
    ass_path.write_text(DUMMY_ASS_CONTENT, encoding="utf-8")
    return str(ass_path)

def run_resizer_script(args):
    """Helper function to run the style_resizer.py script."""
    base_command = [sys.executable, "tools/style_resizer.py"]
    command = base_command + args
    result = subprocess.run(command, capture_output=True, text=True)
    return result

def test_resize_all_styles(setup_test_ass_file):
    """Tests resizing all three tracks at once."""
    ass_file = setup_test_ass_file
    args = ["--ass-file", ass_file, "--orig-size", "10", "--dub-size", "20", "--trans-size", "30"]

    result = run_resizer_script(args)
    assert result.returncode == 0, f"Script failed with output: {result.stderr}"

    subs = pysubs2.load(ass_file)
    assert subs.styles["Style_Orig"].fontsize == 10.0
    assert subs.styles["Style_Dub"].fontsize == 20.0
    assert subs.styles["Style_Trans"].fontsize == 30.0

def test_resize_one_style(setup_test_ass_file):
    """Tests resizing only a single track."""
    ass_file = setup_test_ass_file
    args = ["--ass-file", ass_file, "--dub-size", "99"]

    result = run_resizer_script(args)
    assert result.returncode == 0, f"Script failed with output: {result.stderr}"

    subs = pysubs2.load(ass_file)
    assert subs.styles["Style_Orig"].fontsize == 14.0  # Should be unchanged
    assert subs.styles["Style_Dub"].fontsize == 99.0   # Should be updated
    assert subs.styles["Style_Trans"].fontsize == 22.0 # Should be unchanged

def test_no_args_does_not_change_file(setup_test_ass_file):
    """Tests that running with no size arguments does not change the file."""
    ass_file = setup_test_ass_file

    # Get original content
    with open(ass_file, "r", encoding="utf-8") as f:
        original_content = f.read()

    args = ["--ass-file", ass_file]
    result = run_resizer_script(args)
    assert result.returncode == 0, f"Script failed with output: {result.stderr}"

    # Get new content
    with open(ass_file, "r", encoding="utf-8") as f:
        new_content = f.read()

    assert original_content == new_content

def test_file_not_found():
    """Tests that the script exits with an error for a non-existent file."""
    args = ["--ass-file", "non_existent_file.ass", "--orig-size", "10"]
    result = run_resizer_script(args)
    assert result.returncode != 0
    assert "Error: File not found" in result.stderr
