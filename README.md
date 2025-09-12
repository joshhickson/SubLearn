# SubLearn

*A tool for language learning and film analysis through multi-track subtitles.*

SubLearn is a command-line tool that generates a multi-language subtitle file for three primary use cases: language acquisition, script analysis, and local subtitle alignment. It creates a single, styled `.ass` subtitle file containing up to three tracks for direct comparison.

## Features

-   **Multiple Workflows:** Dedicated modes for language learning, film analysis, and offline subtitle alignment.
-   **Automatic Subtitle Sourcing:** Downloads required subtitle files from OpenSubtitles.
-   **Local File Support:** Prioritizes local `.srt` files and allows for offline-only workflows.
-   **High-Quality Translation:** Uses the DeepL API for accurate machine translations.
-   **AI-Powered Transcription:** Can generate a verbatim transcript from a video file's audio using Faster-Whisper.
-   **Timing Alignment:** Can re-time one subtitle file to match the cadence of another on a line-by-line basis.
-   **Interactive Mode:** Allows you to manually select the correct subtitles from a list of search results.
-   **Batch Processing:** Process an entire directory of video files with a single command.

## Installation & Setup

### 1. Prerequisites

-   Python 3.10+
-   **FFmpeg**: (Optional, for AI Transcription) FFmpeg must be installed and accessible in your system's PATH. Download it from [ffmpeg.org](https://ffmpeg.org/download.html).

### 2. Install Dependencies

From the project root, run:
```bash
pip install -r requirements.txt
```

### 3. Configure the Application

The tool uses a `config.ini` file for API keys and style settings.

1.  Make a copy of the example file: `cp config.ini.example config.ini`
2.  Open `config.ini` and add your API keys.
    -   **OPENSUBTITLES_API_KEY**: Get a key from [OpenSubtitles.org](https://www.opensubtitles.org/).
    -   **DEEPL_API_KEY**: Get a free key from the [DeepL API](https://www.deepl.com/pro-api).
3.  (Optional) Customize subtitle colors and fonts in the `[STYLES]` section.

## Modes of Operation

SubLearn has three distinct workflows.

### 1. Learn Mode (Default)

Designed for **language learning**. It requires a video file and finds perfectly synchronized subtitles by calculating the file's hash. The goal is to ensure the text you read is exactly what you hear.

**Output Tracks:**
1.  **Original Language** (from a hash-synced subtitle file)
2.  **Dub Language** (from a hash-synced or AI-transcribed subtitle file)
3.  **Native Language** (a literal translation of the dub)

### 2. Analysis Mode

Designed for **film analysis**. It allows you to compare the original script to the dubbed script. It works by searching for subtitles by title, which may not be perfectly synchronized, and then re-times the original language subtitle to match the cadence of the dub.

**Output Tracks:**
1.  **Original Language** (from a title search, re-timed to match the dub)
2.  **Dub Language** (from a title search, acts as the timing master)
3.  **Native Language** (a literal translation of the dub)

### 3. Local Alignment Mode

Designed for **offline alignment of two local subtitle files**. This mode does not require a video file or an internet connection (unless translation is also desired). It's a powerful utility for syncing subtitles from different sources.

**Output Tracks:**
1.  **Original Language** (from a local file, re-timed)
2.  **Dub Language** (from a local file, acts as the timing master)
3.  **Native Language** (a literal translation of the dub, optional)

## Usage

### Command-Line Arguments

**Main Arguments:**
-   `path`: (**Required**) Path to a video file/directory (`learn` mode), or an output directory (`analysis` mode). For local alignment, this can be a dummy path (e.g., `./`).
-   `--lang_dub`: (**Required**) The language of the dubbed audio track (e.g., `hu`, `es`).
-   `--lang_orig`: The original language of the film (default: `en`).
-   `--lang_native`: Your native language for translation (default: `EN-US`).
-   `--mode`: `learn` or `analyze`. Determines the operating mode.
-   `--no-translation`: Disables the machine translation track.

**Learn Mode Arguments:**
-   `--interactive`: Manually select subtitles from online search results.
-   `--no-orig-search`: Do not search online for an original language subtitle.
-   `--orig-file`: Path to a local `.srt` file for the original language track.
-   `--dub-file`: Path to a local `.srt` file for the dub track.
-   `--timing-master`: Specify which local file is the timing master (`orig` or `dub`). **Using this with `--orig-file` and `--dub-file` activates the Local Alignment Mode.**

**AI Transcription Arguments:**
-   `--force-transcriber`: Skip online search and transcribe the audio directly.
-   `--fallback-to-transcriber`: Transcribe if a dub subtitle is not found online.
-   `--audio-track <index>`: The index of the audio track to transcribe (default: 0).
-   `--whisper-model <size>`: The Whisper model to use (e.g., `tiny`, `base`).

**Analysis Mode Arguments:**
-   `--query`: The movie title to search for online. Required for analysis mode.

### Examples

**1. Learn Mode (Standard)**

Generate subtitles for a movie with a Hungarian dub, searching online for subs that match the video file's hash.
```bash
python sublearn.py "path/to/your/movie.mkv" --lang_dub hu
```

**2. Learn Mode (with AI Transcription)**

Force the use of the AI transcriber for the most accurate possible transcript of the audio.
```bash
python sublearn.py "path/to/movie.mkv" --lang_dub de --force-transcriber
```

**3. Analysis Mode (Online)**

Search for "The Matrix" subtitles online and align the English track to the Hungarian dub's timing.
```bash
python sublearn.py ./output --mode analyze --query "The Matrix" --lang_orig en --lang_dub hu
```

**4. Local Alignment Mode (Offline)**

Align a local English SRT to a local Hungarian SRT, using the Hungarian file as the timing master.
```bash
python sublearn.py ./dummy.mkv \
    --lang_orig en \
    --lang_dub hu \
    --orig-file "path/to/english.srt" \
    --dub-file "path/to/hungarian.srt" \
    --timing-master dub
```
*(Note: A dummy path is provided as the main argument, but it is not used in this workflow.)*

## Tools

This repository includes standalone scripts in the `tools/` directory for specialized tasks.

### Style Resizer (`tools/style_resizer.py`)

This script allows you to easily change the font size of the three tracks in a SubLearn-generated `.ass` file.

**Usage:**
```bash
python tools/style_resizer.py --ass-file <path_to_ass> --orig-size 16 --dub-size 28
```
Any size argument not provided will be ignored, and the existing size will be kept.
