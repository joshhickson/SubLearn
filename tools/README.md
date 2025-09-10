# SubLearn Tools

This directory contains standalone tools that are part of the SubLearn project but are not part of the main subtitle generation workflow. These tools are designed for specific tasks related to film analysis and learning.

### Context Extractor (`context_extractor.py`)

This tool helps you to perform deep research on specific scenes in a movie by leveraging the power of large language models.

**Usage:**

```bash
python tools/context_extractor.py --srt-file <path_to_srt> --line-number <line_num>
```

**Arguments:**

*   `--srt-file`: The path to the `.srt` subtitle file you want to analyze.
*   `--line-number`: The specific line number in the SRT file that you want to get context for.

**How it works:**

1.  The script will extract the dialogue from the line you specify, as well as the two lines before and after it, to create a contextual snippet.
2.  It will then generate a detailed prompt that you can submit to a large language model like Google's Gemini.
3.  The script will ask you to paste the output from the language model, and it will then format and display the research notes for you.
