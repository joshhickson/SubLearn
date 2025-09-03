import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add the root directory to the Python path to allow importing sublearn
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sublearn

@pytest.fixture
def mock_dependencies(mocker):
    """Mocks the main external dependencies of sublearn.py."""
    mocker.patch('sublearn.translator.translate_subtitle_file', return_value=["Translated text"] * 5)
    mocker.patch('sublearn.fetcher.find_and_download_subtitles', return_value=(None, None))
    mocker.patch('sublearn.merger.create_merged_subtitle_file')

@pytest.fixture
def setup_test_environment(tmp_path):
    """Creates a temporary environment for testing file operations."""
    # Create a dummy video file
    video_path = tmp_path / "test_movie.mkv"
    video_path.touch()

    # Create a dummy config file
    config_path = tmp_path / "config.ini"
    with open(config_path, "w") as f:
        f.write("[API_KEYS]\n")
        f.write("OPENSUBTITLES_API_KEY = fake_key\n")
        f.write("DEEPL_API_KEY = fake_key\n")

    # Create dummy local subtitle files for auto-detection
    movie_dir = tmp_path / "test_movie"
    movie_dir.mkdir()
    (movie_dir / "test_movie.en.srt").touch()
    (movie_dir / "test_movie.hu.srt").touch()

    # Change the current working directory to the temporary directory
    # This makes it easier to test file path logic
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield {
        "video_path": str(video_path),
        "config_path": str(config_path),
        "movie_dir": str(movie_dir)
    }
    # Teardown: change back to the original directory
    os.chdir(original_cwd)


def test_main_workflow_with_local_files(setup_test_environment, mock_dependencies):
    """
    Tests the main workflow when subtitle files are found locally.
    The test relies on the chdir in setup_test_environment for config loading.
    """
    video_path = setup_test_environment["video_path"]

    # Mock sys.argv to simulate command-line arguments
    test_args = ["sublearn.py", video_path, "--lang_dub", "hu"]
    with patch.object(sys, 'argv', test_args):
        # Because the setup_test_environment fixture changes the current working
        # directory to tmp_path, sublearn.main() will automatically find and
        # load the dummy config.ini file created in the test setup.
        try:
            sublearn.main()
        except SystemExit as e:
            # The script calls sys.exit(1) on error. We catch it to prevent
            # the test runner from exiting, but we can assert the exit code.
            # In this successful path, we don't expect a SystemExit.
            pytest.fail(f"sublearn.main() exited unexpectedly with code {e.code}")

    # Assertions
    # 1. Fetcher should NOT have been called because files were detected locally
    sublearn.fetcher.find_and_download_subtitles.assert_not_called()

    # 2. Translator should be called with the path to the local dub file
    expected_dub_path = os.path.join(setup_test_environment["movie_dir"], "test_movie.hu.srt")
    sublearn.translator.translate_subtitle_file.assert_called_once()
    # Check the `filepath` argument specifically
    call_args, call_kwargs = sublearn.translator.translate_subtitle_file.call_args
    assert call_kwargs['filepath'] == expected_dub_path

    # 3. Merger should be called with the correct paths
    expected_orig_path = os.path.join(setup_test_environment["movie_dir"], "test_movie.en.srt")
    expected_ass_path = os.path.join(setup_test_environment["movie_dir"], "test_movie.sublearn.ass")
    sublearn.merger.create_merged_subtitle_file.assert_called_once_with(
        dub_sub_path=expected_dub_path,
        translated_texts=["Translated text"] * 5,
        output_path=expected_ass_path,
        orig_sub_path=expected_orig_path
    )
