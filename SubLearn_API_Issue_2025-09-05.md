
# SubLearn OpenSubtitles API Issue Brief

**Date:** September 5, 2025

## Issue Summary

SubLearn is currently unable to fetch subtitles from the OpenSubtitles API using the movie hash, as no matching subtitles are found for certain video files. The API requests are now working, but the strict hash-based search is too limiting for practical use.

## Objective Redefinition

The true goal is to obtain subtitle tracks that match the movie in general, not necessarily by exact hash. The solution should ensure that English, Hungarian, and translated subtitle tracks are synchronized well enough for language learning, even if they originate from different releases.

## Proposed Solution

1. **General Subtitle Search:**
	- Instead of searching only by movie hash, allow searching for subtitles by movie title, year, and language. This will yield a broader set of subtitle files, including popular releases.

2. **Manual/Heuristic Selection:**
	- Present the user with a list of available subtitle files for each language (e.g., English, Hungarian) and allow manual selection or use heuristics to pick the best match.

3. **Timing Synchronization:**
	- If the selected English subtitle track does not match the timing of the Hungarian/translated tracks, implement a retiming algorithm:
	  - Analyze the timecodes of the Hungarian and English tracks.
	  - Adjust the timing of the English subtitles to align with the Hungarian/translated tracks, using either linear time shifting, scaling, or more advanced matching techniques.

4. **Output Generation:**
	- Merge the retimed English subtitles with the Hungarian and translated tracks into the final multi-track output file.

## Benefits

- Greatly increases the chance of finding usable subtitle files for any movie.
- Allows for practical language learning even when exact hash matches are unavailable.
- Makes the tool more robust and user-friendly.

## Next Steps

- Design and implement the subtitle search and retiming workflow.
- Test with popular movies (e.g., The Matrix) using available subtitle files from OpenSubtitles.

---

**Status:** Solution proposed; pending implementation.
