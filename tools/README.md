# SubLearn Tools

This directory contains standalone scripts that provide supplementary functionality for the SubLearn project.

### Style Resizer (`style_resizer.py`)

This script allows you to easily change the font size of the three tracks (Original, Dub, and Translation) in a SubLearn-generated `.ass` file.

**Usage:**

Run the script from the root of the project directory.

```bash
python tools/style_resizer.py --ass-file <path_to_ass> [options]
```

**Arguments:**
-   `--ass-file`: (**Required**) The path to the `.ass` subtitle file you want to modify.
-   `--orig-size`: (Optional) The new font size for the 'Style_Orig' track.
-   `--dub-size`: (Optional) The new font size for the 'Style_Dub' track.
-   `--trans-size`: (Optional) The new font size for the 'Style_Trans' track.

Any size argument that is not provided will be ignored, and the existing size for that track will be kept.

**Example:**

This command will change the original language font size to 16 and the dub language font size to 28, leaving the translation track unchanged.

```bash
python tools/style_resizer.py --ass-file "path/to/your/subtitle.ass" --orig-size 16 --dub-size 28
```
