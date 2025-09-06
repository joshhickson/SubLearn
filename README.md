# SubLearn

*A tool for language learning and film analysis through multi-track subtitles.*

SubLearn is a command-line tool that generates a multi-language subtitle file for two primary use cases: language acquisition and film analysis. It creates a single `.ass` subtitle file containing up to three tracks for direct comparison.

This allows you to see the original script, the dubbed version you are hearing, and a literal translation all at once, providing a powerful tool for understanding vocabulary, sentence structure, and the creative choices made during the film localization process.

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

## Modes of Operation

SubLearn has two distinct modes, set with the `--mode` flag.

### 1. Learn Mode (Default)

This mode is designed for **language learning**. It requires a local video file and finds perfectly synchronized subtitles by calculating the file's hash. It can also use its built-in AI transcriber to generate a verbatim transcript from the audio if no matching subtitle is found online. The goal is to ensure the text you read is exactly what you hear.

**Output Tracks:**
1.  **Original Language** (from a hash-synced subtitle file)
2.  **Dub Language** (from a hash-synced or AI-transcribed subtitle file)
3.  **Native Language** (a literal translation of the dub)

### 2. Analysis Mode (`--mode analyze`)

This mode is designed for **film analysis**. It allows you to compare the original script to the dubbed script to see what creative choices were made in the translation and localization process. It works by searching for subtitles by title, which may not be perfectly synchronized. It then **re-times** the original language subtitle to match the cadence of the dub language subtitle on a line-by-line basis.

**Output Tracks:**
1.  **Original Language** (from a title search, re-timed to match the dub)
2.  **Dub Language** (from a title search, acts as the timing master)
3.  **Native Language** (a literal translation of the dub)

## Usage

The script is run from the command line. The required arguments change based on the selected mode.

### Basic Syntax

```bash
# Learn Mode (default)
python sublearn.py <path_to_video_or_directory> --lang_dub <dub_lang> [options]

# Analysis Mode
python sublearn.py <path_to_output_directory> --mode analyze --query "Movie Title" --lang_dub <dub_lang> [options]
```

### Arguments

-   `path`: (Required) In `learn` mode, the path to your video file or directory. In `analyze` mode, the path to the directory where output files will be saved.
-   `--mode`: `learn` or `analyze`. Sets the operating mode. Defaults to `learn`.
-   `--lang_dub`: (Required) The language code for the dubbed audio track (e.g., `hu` for Hungarian, `es` for Spanish).
-   `--lang_orig`: The original language of the film. Defaults to `en`.
-   `--lang_native`: The language to translate the dubbed track into. Defaults to `EN-US`.

#### Learn Mode Arguments
-   `--interactive`: Manually select subtitles from a list of online search results.
-   `--no-orig-search`: Do not search for the original language subtitle track.
-   `--force-transcriber`: Force the use of the AI audio transcriber instead of searching online.
-   `--fallback-to-transcriber`: Use the AI transcriber if no suitable dub subtitle is found online.

#### Analysis Mode Arguments
-   `--query`: (Required for Analysis Mode) The movie title to search for.

### Examples

**1. Learn Mode: Processing a Single File (Interactive)**

This will find subtitles for a file, automatically selecting the best match.

```bash
python sublearn.py "/path/to/movies/The.Matrix.1999.mkv" --lang_dub hu
```

**2. Learn Mode: Using the AI Transcriber**

This will generate the dub subtitle directly from your video file's audio track.

```bash
python sublearn.py "/path/to/movies/The.Matrix.1999.mkv" --lang_dub hu --force-transcriber
```

**3. Analysis Mode: Comparing Scripts**

This will search for "The Matrix" subtitles online, let you pick the ones you want, and then align the original English timings to the Hungarian dub timings.

```bash
python sublearn.py ./output --mode analyze --query "The Matrix" --lang_orig en --lang_dub hu
```

## Creating a Standalone Application

For users who do not have Python installed, or for easier distribution, you can package SubLearn into a single standalone executable.

### 1. Build the Executable

First, ensure you have followed the Installation steps to install all dependencies, including `pyinstaller`. Then, run the following command from the root of the project directory:

```bash
pyinstaller --onefile --name sublearn sublearn.py
```

This command will create a `dist/` directory containing the `sublearn` executable (or `sublearn.exe` on Windows).

### 2. Run the Executable

1.  Move the `sublearn` executable from the `dist/` directory to any folder you like.
2.  **Important:** Create a `config.ini` file in the **same folder** as the `sublearn` executable. You can do this by copying the `config.ini.example` from the project and filling in your API keys.
3.  You can now run the application directly from your terminal or command prompt. The usage is the same as the Python script, but you call the executable directly:

    ```bash
    # On macOS or Linux
    ./sublearn "/path/to/movies/" --lang_dub hu --interactive

    # On Windows
    sublearn.exe "C:\path\to\movies\" --lang_dub hu --interactive
    ```

### 3. Debugging

If you encounter any issues, a detailed log file named `sublearn.log` will be created in the same folder as the executable. Please check this file for error messages and tracebacks.
