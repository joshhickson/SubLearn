# SubLearn Subtitle Acquisition Strategy Brief

**Date:** September 6, 2025

## Problem Statement

The current workflow relies on video hash-based logic to fetch matching subtitle files from OpenSubtitles. This approach often fails due to:
- API restrictions on hash-based search for some API keys or accounts
- Hash mismatches between user video files and available subtitles
- Missing subtitle files for specific releases
- Download limits and authentication requirements imposed by OpenSubtitles

### What We Learned from the OpenSubtitles API Documentation

- **Authentication:** The API uses two mechanisms: a static API key (for general search and limited downloads) and a JWT token (for user-authenticated requests, needed for extended downloads and some endpoints).
- **API Key Usage:** The static API key is required for all requests, but some endpoints (like subtitle downloads beyond the basic limit) require user authentication and a JWT token in the `Authorization` header.
- **Download Limits:** Without user authentication, only 5 subtitle downloads per IP per 24 hours are allowed. Setting the API consumer as "Under Development" increases this limit temporarily.
- **User-Agent Header:** All requests must include a `User-Agent` header with the app name and version, or `X-User-Agent` if not possible.
- **Hash-Based Search Limitations:** Hash-based search may be restricted for some API keys, and is not always reliable for finding matching subtitles for every video file.
- **Best Practice:** For broader access and reliability, fetch subtitles by movie title/year and language, and use retiming algorithms to synchronize tracks as needed.

## Objective

Devise a strategy to obtain all necessary subtitle tracks for language learning using only one available SRT file (e.g., Hungarian dub), without relying on video hash-based queries.

## Proposed Solution

1. **Manual SRT Provision:**
   - The user provides a single SRT file (e.g., Hungarian dub) that matches the audio of their video file.

2. **Automated Translation:**
   - Use a translation API (e.g., DeepL) to generate a direct translation of the Hungarian SRT into English, creating a second track (Hun-to-Eng translation).

3. **Generic English SRT Acquisition:**
   - Instead of searching by video hash, fetch a generic English SRT for the movie by title/year from OpenSubtitles or other sources. This file does not need to match the video hash, only the movie in general.
   - If the timing does not match the Hungarian SRT, apply a retiming algorithm to synchronize the English SRT with the Hungarian track.

4. **Track Merging:**
   - Merge the three tracks (Hungarian, translated English, generic English) into a single .ass file for multi-track subtitle display.

## Benefits
- Eliminates dependency on hash-based subtitle search.
- Works with any video file as long as a matching dub SRT is available.
- Maximizes flexibility and success rate for subtitle acquisition and merging.

## Next Steps
- Implement logic to fetch generic English SRTs by title/year.
- Develop and test retiming algorithms for subtitle synchronization.
- Update documentation and user instructions to reflect the new workflow.

---

**Status:** Solution proposed; pending implementation.
