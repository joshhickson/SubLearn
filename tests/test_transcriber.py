import pytest
import os
import transcriber
from unittest.mock import MagicMock, patch

# A simple fixture for mock transcription segments
@pytest.fixture
def mock_segments():
    # Use a class that mimics the structure of faster_whisper's Segment
    class MockSegment:
        def __init__(self, start, end, text):
            self.start = start
            self.end = end
            self.text = text

    segment1 = MockSegment(start=0.0, end=2.5, text=" Hello world. ")
    segment2 = MockSegment(start=2.5, end=5.0, text=" This is a test. ")
    return [segment1, segment2]

def test_format_timestamp():
    assert transcriber.format_timestamp(0) == "00:00:00,000"
    assert transcriber.format_timestamp(12.3456) == "00:00:12,346"
    assert transcriber.format_timestamp(3661.1) == "01:01:01,100"

def test_generate_srt(mock_segments, tmp_path):
    srt_path = tmp_path / "test.srt"
    transcriber.generate_srt(mock_segments, str(srt_path))

    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()

    expected_content = (
        "1\n"
        "00:00:00,000 --> 00:00:02,500\n"
        "Hello world.\n\n"
        "2\n"
        "00:00:02,500 --> 00:00:05,000\n"
        "This is a test.\n\n"
    )
    assert content == expected_content

@patch('transcriber.ffmpeg')
@patch('transcriber.WhisperModel')
@patch('os.remove')
@patch('os.path.exists', return_value=True)
def test_transcribe_audio_track_success(mock_os_path_exists, mock_os_remove, mock_whisper_model, mock_ffmpeg, mock_segments, tmp_path):
    # --- Setup Mocks ---
    # Mock the entire ffmpeg chain
    mock_ffmpeg.input.return_value.output.return_value.overwrite_output.return_value.run.return_value = None

    # Mock WhisperModel instance and its transcribe method
    mock_model_instance = MagicMock()
    mock_info = MagicMock(language='en', language_probability=0.99)
    mock_model_instance.transcribe.return_value = (mock_segments, mock_info)
    mock_whisper_model.return_value = mock_model_instance

    # --- Function Call ---
    video_path = "/fake/video.mkv"
    output_dir = str(tmp_path)
    result_path = transcriber.transcribe_audio_track(
        video_path=video_path,
        language_code="en",
        output_dir=output_dir,
        model_size="tiny",
        audio_track_index=1
    )

    # --- Assertions ---
    # 1. FFmpeg chain was called correctly
    mock_ffmpeg.input.assert_called_once_with(video_path)
    mock_ffmpeg.input.return_value.output.assert_called_once()
    mock_ffmpeg.input.return_value.output.return_value.overwrite_output.assert_called_once()
    mock_ffmpeg.input.return_value.output.return_value.overwrite_output.return_value.run.assert_called_once()


    # 2. WhisperModel was initialized and used
    mock_whisper_model.assert_called_once_with("tiny", device="cpu", compute_type="int8")
    mock_model_instance.transcribe.assert_called_once()

    # 3. SRT file was created and has correct content
    expected_srt_path = os.path.join(output_dir, "video.en.transcribed.srt")
    assert result_path == expected_srt_path
    assert os.path.exists(expected_srt_path)
    with open(expected_srt_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Hello world." in content
    assert "This is a test." in content

    # 4. Cleanup was called
    temp_audio_path = os.path.join(output_dir, "temp_audio.wav")
    mock_os_remove.assert_called_once_with(temp_audio_path)

@patch('transcriber.ffmpeg')
def test_transcribe_audio_track_ffmpeg_error(mock_ffmpeg, tmp_path):
    # --- Setup Mocks ---
    # Simulate an FFmpeg error by making the run call raise an exception
    mock_ffmpeg.input.return_value.output.return_value.overwrite_output.return_value.run.side_effect = transcriber.ffmpeg.Error(
        "mocked ffmpeg error", stdout=None, stderr=b"Error output"
    )

    # --- Function Call ---
    result_path = transcriber.transcribe_audio_track(
        video_path="/fake/video.mkv",
        language_code="en",
        output_dir=str(tmp_path)
    )

    # --- Assertions ---
    assert result_path is None
