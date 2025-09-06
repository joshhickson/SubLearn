# How to Use SubLearn

This guide provides instructions on how to run the SubLearn command-line tool to generate multi-track subtitles for language immersion.

## Prerequisites

- Python 3.x installed on your system.
- `pip` for installing Python packages.
- **FFmpeg**: The AI transcription feature requires FFmpeg to be installed on your system and accessible in your PATH. You can download it from [ffmpeg.org](https://ffmpeg.org/download.html).

## Setup

### 1. Install Dependencies

From the root directory of the project, install the required Python libraries:

```bash
pip install -r requirements.txt
```

### 2. Create and Configure Your `config.ini`

The tool uses a `config.ini` file to manage API keys, subtitle styles, and transcriber settings.

1.  Make a copy of the example file: `cp config.ini.example config.ini`
2.  Open `config.ini` in a text editor.
3.  **Fill in your API keys** under the `[API_KEYS]` section.
    -   **OpenSubtitles API Key**: Get a key by registering for a free account on [OpenSubtitles.org](https://www.opensubtitles.org/) and creating a new API Consumer.
    -   **DeepL API Key**: Get a key from the [DeepL API Free plan](https://www.deepl.com/pro-api) (up to 500,000 characters/month).
4.  (Optional) Customize subtitle appearance under `[STYLES]`.
5.  (Optional) Configure the AI transcription model under `[TRANSCRIBER]`. The `base` model is a good starting point.

## Running the Script

You can run the script from your terminal. The main required argument is the path to your video file or a directory containing video files.

### Command-Line Arguments

-   `path`: (**Required**) The full path to your local video file (e.g., `"C:\Movies\My Movie.mkv"`) or a directory containing video files for batch processing.

**Language Arguments:**
-   `--lang_dub`: (**Required**) The language of the dubbed audio track you want to learn from. Use a two-letter ISO 639-1 code (e.g., `hu` for Hungarian, `es` for Spanish).
-   `--lang_orig`: The original language of the video. Defaults to `en`.
-   `--lang_native`: The language you want the dub track translated into. Defaults to `EN-US` (American English).

**Subtitle Source Arguments:**
-   `--orig-file`: Path to a local `.srt` file to use for the original language track.
-   `--dub-file`: Path to a local `.srt` file to use for the dub language track.
-   `--interactive`: Enable interactive mode to manually select subtitles from a list of online results.
-   `--no-orig-search`: Do not search online for an original language subtitle.

**AI Transcription Arguments:**
-   `--force-transcriber`: Skip the online subtitle search and use the AI transcriber directly.
-   `--fallback-to-transcriber`: If no suitable dub subtitle is found online, automatically run the AI transcriber as a fallback.
-   `--audio-track <index>`: The index of the audio track to transcribe (default: `0`).
-   `--whisper-model <size>`: The Whisper model to use (e.g., `tiny`, `base`, `small`, `medium`). Overrides the `config.ini` setting.

### Example Commands

**Standard Usage (Online Search)**

Generate subtitles for a movie with a Hungarian dub, searching online:
```bash
python sublearn.py "path/to/your/movie.mkv" --lang_dub hu
```

**Batch Processing a Directory**

Process all videos in a directory for Spanish:
```bash
python sublearn.py "path/to/your/movies_folder/" --lang_dub es
```

**Using the AI Transcriber**

If you know the online search will fail, or want the most accurate possible transcript of the audio, you can force the transcriber to run on the second audio track (index 1):
```bash
python sublearn.py "path/to/movie.mkv" --lang_dub de --force-transcriber --audio-track 1
```

Use the transcriber as an automatic fallback if the online search finds nothing:
```bash
python sublearn.py "path/to/movie.mkv" --lang_dub it --fallback-to-transcriber
```

## What to Expect

The script will provide status updates in the terminal. For each video, it will:
1.  Create a dedicated output folder (e.g., `path/to/your/movie/`).
2.  Attempt to find subtitle files based on your arguments (local files, online search).
3.  If configured, run the AI transcriber to generate a dub subtitle from the audio.
4.  Send the text from the dub subtitle to the DeepL API for translation.
5.  Merge the original, dub, and translated subtitle tracks into a single, styled `.ass` file.

The final output file (e.g., `movie.sublearn.ass`) will be saved in the newly created subdirectory, ready to be loaded in a compatible media player like VLC.
