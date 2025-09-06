import ffmpeg
import os
import tempfile
import logging
from faster_whisper import WhisperModel

def format_timestamp(seconds: float) -> str:
    """Converts seconds to SRT timestamp format (HH:MM:SS,ms)."""
    assert seconds >= 0, "non-negative timestamp expected"
    milliseconds = round(seconds * 1000.0)
    hours = milliseconds // 3_600_000
    milliseconds %= 3_600_000
    minutes = milliseconds // 60_000
    milliseconds %= 60_000
    seconds = milliseconds // 1_000
    milliseconds %= 1_000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def generate_srt(segments: list, output_path: str):
    """Generates an SRT file from whisper transcription segments."""
    with open(output_path, "w", encoding="utf-8") as srt_file:
        for i, segment in enumerate(segments):
            start_time = format_timestamp(segment.start)
            end_time = format_timestamp(segment.end)
            text = segment.text.strip()
            srt_file.write(f"{i + 1}\n")
            srt_file.write(f"{start_time} --> {end_time}\n")
            srt_file.write(f"{text}\n\n")
    logging.info(f"SRT file generated at {output_path}")

def transcribe_audio_track(
    video_path: str,
    language_code: str,
    output_dir: str,
    model_size: str = "base",
    audio_track_index: int = 0
) -> str | None:
    """
    Extracts an audio track from a video, transcribes it, and returns the SRT file path.
    """
    logging.info(f"Starting transcription for {video_path}...")
    logging.info(f"Using Whisper model: {model_size}, Language: {language_code}, Audio Track: {audio_track_index}")

    # 1. Extract audio using ffmpeg
    audio_file_path = os.path.join(output_dir, "temp_audio.wav")
    try:
        logging.info("Extracting audio track...")
        (
            ffmpeg
            .input(video_path)
            .output(audio_file_path, acodec='pcm_s16le', ac=1, ar='16000', map=f'0:a:{audio_track_index}')
            .overwrite_output()
            .run(quiet=True, capture_stdout=True, capture_stderr=True)
        )
        logging.info(f"Audio track extracted successfully to {audio_file_path}")
    except ffmpeg.Error as e:
        logging.error("FFmpeg error during audio extraction:")
        logging.error(e.stderr.decode())
        return None

    # 2. Transcribe using faster-whisper
    try:
        logging.info("Loading Whisper model...")
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        logging.info("Model loaded. Starting transcription...")
        segments, info = model.transcribe(audio_file_path, language=language_code)
        logging.info(f"Detected language '{info.language}' with probability {info.language_probability}")

        # 3. Generate SRT file
        video_filename_no_ext = os.path.splitext(os.path.basename(video_path))[0]
        srt_path = os.path.join(output_dir, f"{video_filename_no_ext}.{language_code}.transcribed.srt")
        generate_srt(list(segments), srt_path)
        return srt_path

    except Exception as e:
        logging.error(f"Error during transcription: {e}", exc_info=True)
        return None
    finally:
        # 4. Clean up temporary audio file
        if os.path.exists(audio_file_path):
            os.remove(audio_file_path)
            logging.info(f"Cleaned up temporary audio file: {audio_file_path}")
