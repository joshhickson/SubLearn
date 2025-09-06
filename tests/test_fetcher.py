import pytest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sublearn import _select_best_dub_subtitle
import fetcher


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

@patch('fetcher.requests.get')
def test_search_subtitles_by_query(mock_get):
    """Tests the query-based subtitle search function."""
    # --- Setup Mock ---
    mock_response = MagicMock()
    mock_api_data = {
        "total_pages": 1,
        "total_count": 1,
        "data": [{"id": "12345", "attributes": {"language": "en", "release": "Test Release"}}]
    }
    mock_response.json.return_value = mock_api_data
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    # --- Function Call ---
    results = fetcher.search_subtitles_by_query(
        query="The Matrix",
        language="en",
        api_key="fake_api_key"
    )

    # --- Assertions ---
    # 1. Assert that requests.get was called correctly
    expected_url = "https://api.opensubtitles.com/api/v1/subtitles"
    expected_params = {"query": "The Matrix", "languages": "en"}
    mock_get.assert_called_once()
    call_args = mock_get.call_args
    assert call_args.args[0] == expected_url
    assert call_args.kwargs['params'] == expected_params
    assert call_args.kwargs['headers']['Api-Key'] == "fake_api_key"

    # 2. Assert that the function returned the correct data
    assert len(results) == 1
    assert results[0]['id'] == "12345"
    assert results[0]['attributes']['release'] == "Test Release"
