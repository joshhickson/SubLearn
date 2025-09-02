# How to Use SubLearn

This guide provides instructions on how to run the SubLearn command-line tool to generate multi-track subtitles.

## Prerequisites

- Python 3.x installed on your system.
- `pip` for installing Python packages.

## Setup

### 1. Install Dependencies

From the root directory of the project, install the required Python libraries using the provided `requirements.txt` file:

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

The tool requires API keys for two services: **OpenSubtitles.org** and **DeepL**.

For this prototype, you must edit the `sublearn.py` script and insert your API keys directly into the file.

Open `sublearn.py` and modify these lines:

```python
# sublearn.py

# --- Configuration ---
# In Phase 1, API keys are hardcoded.
# In Phase 2, these will be moved to a configuration file.
OPENSUBTITLES_API_KEY = "YOUR_OPENSUBTITLES_API_KEY_HERE"
DEEPL_API_KEY = "YOUR_DEEPL_API_KEY_HERE"
```

- **OpenSubtitles API Key**: You can get a key by registering for a free account on [OpenSubtitles.org](https://www.opensubtitles.org/) and creating a new API Consumer in your user profile settings.
- **DeepL API Key**: You can get a key by signing up for the DeepL API Free plan on the [DeepL website](https://www.deepl.com/pro-api). The free plan allows up to 500,000 characters per month, which is sufficient for personal use.

## Running the Script

You can run the script from your terminal. The main required argument is the path to your video file.

### Command-Line Arguments

- `video_path`: (**Required**) The full path to your local video file. If the path contains spaces, enclose it in quotes (e.g., `"C:\My Movies\My Movie.mkv"`).
- `--lang_dub`: (**Required**) The language of the dubbed audio track you want to learn from. Use a two-letter ISO 639-1 code (e.g., `hu` for Hungarian, `es` for Spanish, `de` for German).
- `--lang_orig`: The original language of the video. Defaults to `en` (English).
- `--lang_native`: The language you want the dub track to be translated into. This must be a language code supported by DeepL. Defaults to `EN-US` (American English).

### Example Command

To generate subtitles for a movie file with a Hungarian dub, run the following command in your terminal:

```bash
python sublearn.py "path/to/your/movie.mkv" --lang_dub hu
```

If you wanted to process a movie with a Spanish dub and translate it into German, the command would be:

```bash
python sublearn.py "path/to/your/movie.mkv" --lang_orig en --lang_dub es --lang_native DE
```

## What to Expect

The script will provide status updates in the terminal as it performs the following steps:
1. Calculates a unique hash of your video file.
2. Queries OpenSubtitles to find and download the best-matching original and dub language subtitles.
3. Sends the text from the dub subtitle to DeepL for translation.
4. Merges all three subtitle tracks into a single file with custom styling and positioning.

A new file named `[your_movie_name].sublearn.ass` will be created in the same directory as your video file. You can load this `.ass` file in a compatible media player (like VLC or Plex Media Player) to view the multi-track subtitles.
