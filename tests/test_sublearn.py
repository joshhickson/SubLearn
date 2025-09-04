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
    mocker.patch('sublearn.merger.create_merged_subtitle_file')
    # Mock the fetcher module functions
    mocker.patch('sublearn.fetcher.get_movie_hash', return_value="dummy_hash")
    mocker.patch('sublearn.fetcher.search_subtitles', return_value=([], []))  # Default: find no subs
    # The download function will just return the path it was given, simulating a successful download
    mocker.patch('sublearn.fetcher.download_subtitle', side_effect=lambda data, api_key, save_path: save_path)

@pytest.fixture
def setup_test_environment(tmp_path, mocker):
    """Creates a temporary environment for testing file operations."""
    # Mock the base path to point to our temporary directory
    mocker.patch('sublearn.get_base_path', return_value=str(tmp_path))

    # Create a dummy video file
    video_path = tmp_path / "test_movie.mkv"
    video_path.touch()

    # Create a dummy config file in the mocked base path
    config_path = tmp_path / "config.ini"
    config_path.write_text("[API_KEYS]\nOPENSUBTITLES_API_KEY = fake_key\nDEEPL_API_KEY = fake_key\n")

    # Create dummy local subtitle files for auto-detection
    movie_dir = tmp_path / "test_movie"
    movie_dir.mkdir()
    (movie_dir / "test_movie.en.srt").touch()
    (movie_dir / "test_movie.hu.srt").touch()

    yield {
        "video_path": str(video_path),
        "config_path": str(config_path),
        "movie_dir": str(movie_dir)
    }


def test_process_video_file_local_found(setup_test_environment, mock_dependencies):
    """
    Tests the process_video_file function when subtitle files are found locally.
    """
    video_path = setup_test_environment["video_path"]
    args = MagicMock()
    args.lang_orig = "en"
    args.lang_dub = "hu"
    args.lang_native = "EN-US"
    args.interactive = False
    args.no_orig_search = False

    api_keys = {'opensubtitles': 'fake_key', 'deepl': 'fake_key'}

    # --- Run the function to be tested ---
    sublearn.process_video_file(video_path, args, api_keys)

    # --- Assertions ---
    # 1. Fetcher's search function should NOT have been called
    sublearn.fetcher.search_subtitles.assert_not_called()

    # 2. Translator should be called with the correct local dub file path
    expected_dub_path = os.path.join(setup_test_environment["movie_dir"], "test_movie.hu.srt")
    sublearn.translator.translate_subtitle_file.assert_called_once()
    call_kwargs = sublearn.translator.translate_subtitle_file.call_args.kwargs
    assert call_kwargs['filepath'] == expected_dub_path
    assert call_kwargs['api_key'] == 'fake_key'

    # 3. Merger should be called with the correct paths
    expected_orig_path = os.path.join(setup_test_environment["movie_dir"], "test_movie.en.srt")
    expected_ass_path = os.path.join(setup_test_environment["movie_dir"], "test_movie.sublearn.ass")
    sublearn.merger.create_merged_subtitle_file.assert_called_once_with(
        dub_sub_path=expected_dub_path,
        translated_texts=["Translated text"] * 5,
        output_path=expected_ass_path,
        orig_sub_path=expected_orig_path
    )

def test_process_video_file_interactive_online_found(setup_test_environment, mock_dependencies, mocker):
    """
    Tests the process_video_file function with interactive selection for online subs.
    """
    video_path = setup_test_environment["video_path"]

    # Remove local files to force an online search
    for item in os.listdir(setup_test_environment["movie_dir"]):
        os.remove(os.path.join(setup_test_environment["movie_dir"], item))

    args = MagicMock()
    args.lang_orig = "en"
    args.lang_dub = "hu"
    args.lang_native = "EN-US"
    args.interactive = True
    args.no_orig_search = False

    api_keys = {'opensubtitles': 'fake_key', 'deepl': 'fake_key'}

    # --- Setup Mocks for this specific test ---
    sample_orig_subs = [{"attributes": {"release": "Orig A", "files": [{"file_id": 101}], "download_count": 1}}]
    sample_dub_subs = [{"attributes": {"release": "Dub X", "files": [{"file_id": 201}], "download_count": 2}}, {"attributes": {"release": "Dub Y", "files": [{"file_id": 202}], "download_count": 3}}]
    sublearn.fetcher.search_subtitles.return_value = (sample_orig_subs, sample_dub_subs)

    # Mock user input to select the 1st original and 2nd dub
    mocker.patch('builtins.input', side_effect=['1', '2'])

    # --- Run the function ---
    sublearn.process_video_file(video_path, args, api_keys)

    # --- Assertions ---
    # 1. Search should have been called
    sublearn.fetcher.search_subtitles.assert_called_once()

    # 2. Download should have been called with the correct, user-selected metadata
    expected_calls = [
        mocker.call(sample_orig_subs[0], 'fake_key', os.path.join(setup_test_environment["movie_dir"], "test_movie.en.srt")),
        mocker.call(sample_dub_subs[1], 'fake_key', os.path.join(setup_test_environment["movie_dir"], "test_movie.hu.srt")),
    ]
    sublearn.fetcher.download_subtitle.assert_has_calls(expected_calls, any_order=True)
    assert sublearn.fetcher.download_subtitle.call_count == 2

    # 3. Merger should be called
    sublearn.merger.create_merged_subtitle_file.assert_called_once()

@patch('sublearn.process_video_file')
def test_main_batch_processing(mock_process_video, tmp_path, mocker):
    """
    Tests that the main function correctly identifies and loops through video files in a directory.
    """
    # --- Setup test environment ---
    video_dir = tmp_path / "batch_test"
    video_dir.mkdir()
    (video_dir / "video1.mkv").touch()
    (video_dir / "video2.mp4").touch()
    (video_dir / "notes.txt").touch() # A non-video file that should be ignored

    # Mock get_base_path to point to our temporary directory
    mocker.patch('sublearn.get_base_path', return_value=str(tmp_path))

    # Create a dummy config file in the mocked base path
    (tmp_path / "config.ini").write_text("[API_KEYS]\nOPENSUBTITLES_API_KEY=fake\nDEEPL_API_KEY=fake")

    # --- Run the main function with the directory path ---
    test_args = ["sublearn.py", str(video_dir), "--lang_dub", "hu"]
    with patch.object(sys, 'argv', test_args):
        try:
            sublearn.main()
        except SystemExit:
            pytest.fail("sublearn.main() exited unexpectedly in batch mode test.")

    # --- Assertions ---
    # Assert that process_video_file was called exactly twice
    assert mock_process_video.call_count == 2

    # Assert that it was called with the correct video file paths
    call_paths = [call.args[0] for call in mock_process_video.call_args_list]
    expected_paths = [str(video_dir / "video1.mkv"), str(video_dir / "video2.mp4")]
    assert sorted(call_paths) == sorted(expected_paths)
