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
    args.orig_file = None
    args.dub_file = None
    # Add transcriber args
    args.force_transcriber = False
    args.fallback_to_transcriber = False

    api_keys = {'opensubtitles': 'fake_key', 'deepl': 'fake_key'}
    styles = {
        'dub_fontsize': 24, 'dub_color': (255, 255, 0), 'dub_alignment': 8, 'dub_marginv': 10,
        'trans_fontsize': 22, 'trans_color': (0, 255, 255), 'trans_alignment': 8, 'trans_marginv': 40,
        'orig_fontsize': 14, 'orig_color': (255, 255, 255), 'orig_alignment': 2, 'orig_marginv': 10,
    }
    transcriber_settings = {'model_size': 'tiny'}

    # --- Run the function to be tested ---
    sublearn.process_video_file(video_path, args, api_keys, styles, transcriber_settings)

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
    sublearn.merger.create_merged_subtitle_file.assert_called_once()
    call_kwargs = sublearn.merger.create_merged_subtitle_file.call_args.kwargs
    assert call_kwargs['dub_sub_path'] == expected_dub_path
    assert call_kwargs['output_path'] == expected_ass_path
    assert 'styles' in call_kwargs

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
    args.orig_file = None
    args.dub_file = None
    # Add transcriber args
    args.force_transcriber = False
    args.fallback_to_transcriber = False

    api_keys = {'opensubtitles': 'fake_key', 'deepl': 'fake_key'}
    styles = {
        'dub_fontsize': 24, 'dub_color': (255, 255, 0), 'dub_alignment': 8, 'dub_marginv': 10,
        'trans_fontsize': 22, 'trans_color': (0, 255, 255), 'trans_alignment': 8, 'trans_marginv': 40,
        'orig_fontsize': 14, 'orig_color': (255, 255, 255), 'orig_alignment': 2, 'orig_marginv': 10,
    }
    transcriber_settings = {'model_size': 'tiny'}

    # --- Setup Mocks for this specific test ---
    sample_orig_subs = [{"attributes": {"release": "Orig A", "files": [{"file_id": 101}], "download_count": 1}}]
    sample_dub_subs = [{"attributes": {"release": "Dub X", "files": [{"file_id": 201}], "download_count": 2}}, {"attributes": {"release": "Dub Y", "files": [{"file_id": 202}], "download_count": 3}}]
    sublearn.fetcher.search_subtitles.return_value = (sample_orig_subs, sample_dub_subs)

    # Mock user input to select the 1st original and 2nd dub
    mocker.patch('builtins.input', side_effect=['1', '2'])

    # --- Run the function ---
    sublearn.process_video_file(video_path, args, api_keys, styles, transcriber_settings)

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
    call_kwargs = sublearn.merger.create_merged_subtitle_file.call_args.kwargs
    assert 'styles' in call_kwargs

def test_process_video_file_with_arg(setup_test_environment, mock_dependencies):
    """
    Tests that --dub-file argument is prioritized over local file detection.
    """
    video_path = setup_test_environment["video_path"]

    # Create a dummy SRT file to be specified by the argument
    user_srt_path = os.path.join(setup_test_environment["movie_dir"], "user_provided.srt")
    with open(user_srt_path, "w") as f:
        f.write("test subtitle")

    args = MagicMock()
    args.lang_orig = "en"
    args.lang_dub = "hu"
    args.lang_native = "EN-US"
    args.interactive = False
    args.no_orig_search = False
    args.orig_file = None
    args.dub_file = str(user_srt_path) # Use the user-provided file
    # Add transcriber args
    args.force_transcriber = False
    args.fallback_to_transcriber = False

    api_keys = {'opensubtitles': 'fake_key', 'deepl': 'fake_key'}
    styles = {
        'dub_fontsize': 24, 'dub_color': (255, 255, 0), 'dub_alignment': 8, 'dub_marginv': 10,
        'trans_fontsize': 22, 'trans_color': (0, 255, 255), 'trans_alignment': 8, 'trans_marginv': 40,
        'orig_fontsize': 14, 'orig_color': (255, 255, 255), 'orig_alignment': 2, 'orig_marginv': 10,
    }
    transcriber_settings = {'model_size': 'tiny'}

    # --- Run the function ---
    sublearn.process_video_file(video_path, args, api_keys, styles, transcriber_settings)

    # --- Assertions ---
    # 1. Translator should have been called with the user-provided file, not the auto-detected one
    sublearn.translator.translate_subtitle_file.assert_called_once()
    call_kwargs = sublearn.translator.translate_subtitle_file.call_args.kwargs
    assert call_kwargs['filepath'] == str(user_srt_path)

    # 2. Merger should also be called with the user-provided file and styles
    sublearn.merger.create_merged_subtitle_file.assert_called_once()
    call_kwargs = sublearn.merger.create_merged_subtitle_file.call_args.kwargs
    assert call_kwargs['dub_sub_path'] == str(user_srt_path)
    assert 'styles' in call_kwargs

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
    (tmp_path / "config.ini").write_text("[API_KEYS]\nOPENSUBTITLES_API_KEY=fake\nDEEPL_API_KEY=fake\n[TRANSCRIBER]\nmodel_size=tiny")

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

    # Assert that it was called with the correct video file paths and settings
    call_paths = [call.args[0] for call in mock_process_video.call_args_list]
    expected_paths = [str(video_dir / "video1.mkv"), str(video_dir / "video2.mp4")]
    assert sorted(call_paths) == sorted(expected_paths)
    # Check that the settings dicts were passed in each call
    for call in mock_process_video.call_args_list:
        styles_arg = call.args[3] # styles is the 4th positional argument
        transcriber_arg = call.args[4] # transcriber_settings is the 5th
        assert isinstance(styles_arg, dict)
        assert 'orig_alignment' in styles_arg
        assert isinstance(transcriber_arg, dict)
        assert 'model_size' in transcriber_arg

@patch('sublearn.merger')
@patch('sublearn.translator')
@patch('sublearn.aligner')
@patch('sublearn.fetcher')
@patch('builtins.input', side_effect=['1', '1']) # Select first option for both prompts
def test_main_analysis_mode(mock_input, mock_fetcher, mock_aligner, mock_translator, mock_merger, tmp_path, mocker):
    """
    Tests the main function's dispatch to the analysis workflow.
    """
    # --- Setup Mocks ---
    mock_fetcher.search_subtitles_by_query.return_value = [{"attributes": {"release": "Release", "files": [{"file_id": 123}]}}]
    mock_fetcher.download_subtitle.side_effect = ["/tmp/orig.srt", "/tmp/dub.srt"]
    mocker.patch('sublearn.pysubs2.load')
    mocker.patch('sublearn.os.remove')

    # Mock get_base_path and config file
    mocker.patch('sublearn.get_base_path', return_value=str(tmp_path))
    (tmp_path / "config.ini").write_text("[API_KEYS]\nOPENSUBTITLES_API_KEY=fake\nDEEPL_API_KEY=fake")

    # --- Run the main function with analysis mode args ---
    output_dir = tmp_path / "analysis_output"
    test_args = [
        "sublearn.py", str(output_dir),
        "--mode", "analyze",
        "--query", "The Matrix",
        "--lang_orig", "en",
        "--lang_dub", "hu"
    ]
    with patch.object(sys, 'argv', test_args):
        try:
            sublearn.main()
        except SystemExit:
            pytest.fail("sublearn.main() exited unexpectedly in analysis mode test.")

    # --- Assertions ---
    # 1. Fetcher was called twice to search by query
    assert mock_fetcher.search_subtitles_by_query.call_count == 2
    mock_fetcher.search_subtitles_by_query.assert_any_call("The Matrix", "en", "fake")
    mock_fetcher.search_subtitles_by_query.assert_any_call("The Matrix", "hu", "fake")

    # 2. Aligner was called
    mock_aligner.align_by_index.assert_called_once()

    # 3. Translator was called
    mock_translator.translate_subtitle_file.assert_called_once()

    # 4. Merger was called
    mock_merger.create_merged_subtitle_file.assert_called_once()
