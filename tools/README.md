# SubLearn Tools

This directory contains standalone tools that are part of the SubLearn project but are not part of the main subtitle generation workflow. These tools are designed for specific tasks related to film analysis and learning.

### Context Extractor (`context_extractor.py`)

This tool helps you to perform deep research on specific scenes in a movie by leveraging the power of large language models.

**Usage:**

```bash
python tools/context_extractor.py --srt-file <path_to_srt> --line-number <line_num> --movie-title "Movie Title (Year)"
```

**Arguments:**

*   `--srt-file`: The path to the `.srt` subtitle file you want to analyze.
*   `--line-number`: The specific line number in the SRT file that you want to get context for.
*   `--movie-title`: The full title of the movie, preferably with the year, for more accurate research.

**How it works:**

1.  The script extracts the dialogue from the line you specify, as well as the two lines before and after it, to create a contextual snippet.
2.  It generates a detailed research prompt customized with your movie's title.
3.  The script prints the prompt to your console. You can copy this and submit it to a large language model (like Google Gemini, ChatGPT, etc.).
4.  After you get the response from the model, you paste it back into the terminal.
5.  The script then displays the information in a formatted "X-Ray Analysis" view for your scene.
