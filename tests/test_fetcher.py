import pytest
from fetcher import _select_best_dub_subtitle

@pytest.fixture
def sample_subtitles():
    """Provides a sample list of subtitle data for testing."""
    return [
        {
            "attributes": {
                "release": "The.Movie.2023.1080p.BluRay",
                "comments": "Standard version.",
                "download_count": 100,
            }
        },
        {
            "attributes": {
                "release": "The.Movie.2023.720p.WEB-DL.Hun.Dub",
                "comments": "Hungarian dubbing.",
                "download_count": 500,
            }
        },
        {
            "attributes": {
                "release": "The.Movie.2023.Foreign.Retail.DVD",
                "comments": "Official release with hungarian szinkron.",
                "download_count": 200,
            }
        },
        {
            "attributes": {
                "release": "The.Movie.2023.IMAX.Edition",
                "comments": "Just a high quality rip.",
                "download_count": 1500,
            }
        },
    ]

def test_select_best_dub_subtitle(sample_subtitles):
    """
    Tests that the subtitle with the best score (based on keywords and downloads) is selected.
    """
    dub_keywords = ["dub", "dubbed", "szinkron"]

    # --- Test Case 1: "dub" in release name should be heavily weighted ---
    # The subtitle with "Hun.Dub" in the release name should win despite lower downloads
    # compared to the IMAX version, because keywords in the release name have a high score.
    best_sub = _select_best_dub_subtitle(sample_subtitles, dub_keywords)
    assert best_sub is not None
    assert "Hun.Dub" in best_sub['attributes']['release']

    # --- Test Case 2: "szinkron" in comments should be weighted ---
    # Create a new list where the "dub" release is removed.
    # The subtitle with "szinkron" in the comments should now be selected.
    filtered_subs = [s for s in sample_subtitles if "Hun.Dub" not in s['attributes']['release']]
    best_sub_comment = _select_best_dub_subtitle(filtered_subs, dub_keywords)
    assert best_sub_comment is not None
    assert "szinkron" in best_sub_comment['attributes']['comments']

    # --- Test Case 3: Fallback to highest download count ---
    # Create a list with no keywords, where the highest download count should win.
    no_keyword_subs = [
        {"attributes": {"release": "A", "comments": "a", "download_count": 100}},
        {"attributes": {"release": "B", "comments": "b", "download_count": 500}},
        {"attributes": {"release": "C", "comments": "c", "download_count": 200}},
    ]
    best_sub_downloads = _select_best_dub_subtitle(no_keyword_subs, dub_keywords)
    assert best_sub_downloads is not None
    assert best_sub_downloads['attributes']['download_count'] == 500

def test_select_best_dub_subtitle_no_match():
    """Tests that the function returns the highest downloaded sub if no keywords match."""
    no_keyword_subs = [
        {"attributes": {"release": "A", "comments": "a", "download_count": 100}},
        {"attributes": {"release": "B", "comments": "b", "download_count": 500}},
    ]
    dub_keywords = ["keyword-that-doesnt-exist"]
    best_sub = _select_best_dub_subtitle(no_keyword_subs, dub_keywords)
    assert best_sub is not None
    assert best_sub['attributes']['download_count'] == 500
