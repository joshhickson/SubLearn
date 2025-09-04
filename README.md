# SubLearn

*Inventing a new way to learn from and truly understand foreign language audio tracks in films and TV shows.*

SubLearn is a command-line tool that generates a multi-language subtitle file designed to help with language acquisition. For a given video file with a dubbed audio track, it creates a single `.ass` subtitle file containing up to three tracks:
1.  The original language dialogue (e.g., English).
2.  The dubbed language dialogue (e.g., Hungarian).
3.  A direct, word-for-word translation of the dubbed dialogue into your native language.

This allows you to see the original script, the dubbed version you are hearing, and a literal translation all at once, providing a powerful tool for understanding vocabulary and sentence structure.

## Features

-   **Automatic Subtitle Sourcing:** Downloads the required subtitle files from OpenSubtitles.
-   **Local File Detection:** Automatically uses existing local `.srt` files if they are found.
-   **High-Quality Translation:** Uses the DeepL API for accurate translations.
-   **Interactive Mode:** Allows you to manually select the correct subtitles from a list of search results.
-   **Batch Processing:** Process an entire directory of video files with a single command.
-   **Organized Output:** Creates a dedicated folder for each video's subtitles.

## Installation

1.  **Prerequisites:** Make sure you have Python 3.10+ installed on your system.

2.  **Clone the Repository:**
    ```bash
    git clone https://github.com/your-username/sublearn.git
    cd sublearn
    ```

3.  **Install Dependencies:** Install the required Python packages using pip.
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

Before running the script, you need to provide your API keys for OpenSubtitles and DeepL.

1.  **Create the Config File:** Copy the example configuration file.
    ```bash
    cp config.ini.example config.ini
    ```

2.  **Edit the Config File:** Open `config.ini` in a text editor and replace the placeholder text with your actual API keys.
    ```ini
    [API_KEYS]
    OPENSUBTITLES_API_KEY = YOUR_API_KEY_HERE
    DEEPL_API_KEY = YOUR_API_KEY_HERE
    ```
    *Your `config.ini` file is ignored by git, so your keys will not be committed.*

## Usage

The script is run from the command line, providing the path to a video file or a directory.

### Basic Syntax

```bash
python sublearn.py <path_to_video_or_directory> --lang_dub <dub_language_code> [options]
```

### Arguments

-   `path`: (Required) The full path to your video file or a directory containing video files.
-   `--lang_dub`: (Required) The language code for the dubbed audio track you want to study (e.g., `hu` for Hungarian, `es` for Spanish).
-   `--lang_orig`: The original language of the film. Defaults to `en`.
-   `--lang_native`: The language to translate the dubbed track into. Defaults to `EN-US`.
-   `--interactive`: Use this flag to manually select subtitles from a list of online search results. Recommended for accuracy.
-   `--no-orig-search`: Use this flag to prevent the script from searching for the original language subtitle track.

### Examples

**1. Processing a Single File (Automatic Mode)**

This will find subtitles for a file, automatically selecting the best match.

```bash
python sublearn.py "/path/to/movies/The.Matrix.1999.mkv" --lang_dub hu
```

**2. Processing a Single File (Interactive Mode)**

This will present you with a list of found subtitles to choose from, which is the recommended mode for best results.

```bash
python sublearn.py "/path/to/movies/The.Matrix.1999.mkv" --lang_dub hu --interactive
```

**3. Batch Processing a Directory**

This will find and process all video files (`.mkv`, `.mp4`, etc.) in the specified directory.

```bash
python sublearn.py "/path/to/movies/" --lang_dub hu --interactive
```
