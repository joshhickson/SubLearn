# SubLearn

*A tool for language learning and film analysis through multi-track subtitles.*

SubLearn is a command-line tool that generates a multi-language subtitle file for three primary use cases: language acquisition, script analysis, and local subtitle alignment. It creates a single, styled `.ass` subtitle file containing up to three tracks for direct comparison.

## Features

-   **Multiple Workflows:** Dedicated modes for language learning, online analysis, and offline subtitle alignment.
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

SubLearn has three distinct workflows, chosen with the `--mode` flag.

### 1. Learn Mode (`--mode learn`, Default)

Designed for **language learning**. It requires a video file and finds perfectly synchronized subtitles by calculating the file's hash.
- **Input:** Path to a video file or a directory of videos.
- **Output:** A styled `.ass` file in a sub-directory named after the video.

### 2. Query & Align Mode (`--mode query-align`)

Designed for **film analysis**. It allows you to compare the original script to the dubbed script by searching for both online and then aligning them.
- **Input:** An output directory and a `--query` string for the movie title.
- **Output:** A single `.ass` file in the specified output directory.

### 3. Local Align Mode (`--mode align`)

Designed for **offline alignment of two local subtitle files**. This is a powerful utility for syncing subtitles from different sources without a video file.
- **Input:** An output directory, two local `.srt` files, and a designated timing master.
- **Output:** A single `.ass` file in the specified output directory.

## Usage

### Command-Line Arguments

**Main Arguments:**
-   `path`: (**Required**) The meaning of this argument changes based on the mode:
    -   `learn`: Path to a video file or directory.
    -   `query-align` or `align`: Path to the desired output directory.
-   `--lang_dub`: (**Required**) The language of the dubbed audio track (e.g., `hu`, `es`).
-   `--lang_orig`: The original language of the film (default: `en`).
-   `--lang_native`: Your native language for translation (default: `EN-US`).
-   `--mode`: `learn`, `query-align`, or `align`. Determines the operating mode.
-   `--no-translation`: Disables the machine translation track.

**Learn Mode Arguments:**
-   `--interactive`: Manually select subtitles from online search results.
-   `--no-orig-search`: Do not search online for an original language subtitle.
-   `--force-transcriber`, `--fallback-to-transcriber`: Control the use of the AI audio transcriber.
-   `--audio-track <index>`, `--whisper-model <size>`: Configure the transcriber settings.

**Local File Arguments (for `learn` and `align` modes):**
-   `--orig-file`: Path to a local `.srt` file for the original language track.
-   `--dub-file`: Path to a local `.srt` file for the dub track.

**Query & Align Mode Arguments:**
-   `--query`: (**Required**) The movie title to search for online.

**Local Align Mode Arguments:**
-   `--timing-master`: (**Required**) Specify which file is the timing master (`orig` or `dub`).
-   `--orig-file` and `--dub-file` are also required for this mode.

### Examples

**1. Learn Mode (Standard)**
Generate subtitles for a movie, searching online for subs that match the video file's hash.
```bash
python sublearn.py "path/to/your/movie.mkv" --lang_dub hu
```

**2. Query & Align Mode (Online Analysis)**
Search for "The Matrix" subtitles online and align the English track to the Hungarian dub's timing.
```bash
python sublearn.py ./output --mode query-align --query "The Matrix" --lang_orig en --lang_dub hu
```

**3. Local Align Mode (Offline)**
Align a local English SRT to a local Hungarian SRT, using the Hungarian file as the timing master.
```bash
python sublearn.py ./output --mode align \
    --orig-file "path/to/english.srt" \
    --dub-file "path/to/hungarian.srt" \
    --timing-master dub
```

## Tools

This repository includes standalone scripts in the `tools/` directory for specialized tasks.

### Style Resizer (`tools/style_resizer.py`)

This script allows you to easily change the font size of the three tracks in a SubLearn-generated `.ass` file.

**Usage:**
```bash
python tools/style_resizer.py --ass-file <path_to_ass> --orig-size 16 --dub-size 28
```
Any size argument not provided will be ignored, and the existing size will be kept.
