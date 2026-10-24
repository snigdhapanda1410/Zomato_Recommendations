"""
Edge case and corner scenario tests (Phase 6, Task 6.3: E1 to E10).

Verifies the robustness of the Zomato AI Restaurant Recommendation System
under adverse, boundary, and unexpected inputs.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pandas as pd
import pytest

from src.data.loader import DatasetEmptyError, DatasetLoader, DatasetLoadError
from src.data.preprocessor import DataPreprocessor
from src.filters.filter_engine import FilterEngine, UserPreferences
from src.llm.llm_client import LLMAPIKeyError, LLMClient, LLMError
from src.llm.prompt_builder import PromptBuilder
from src.llm.response_parser import Recommendation, ResponseParser
from src.recommendation.engine import RecommendationEngine, RecommendationResult
from src.utils.config import AppConfig


@pytest.fixture
def sample_dataset() -> pd.DataFrame:
    """Standard preprocessed dataset for edge case testing."""
    return pd.DataFrame(
        [
            {
                "name": "Truffles",
                "location": "Koramangala",
                "cuisines": "American, Italian",
                "cost_for_two": 800,
                "rating": 4.6,
                "votes": 5000,
                "budget_category": "Medium",
                "online_order": True,
                "book_table": False,
            },
            {
                "name": "Toit",
                "location": "Indiranagar",
                "cuisines": "Italian, Continental, Craft Beer",
                "cost_for_two": 1500,
                "rating": 4.7,
                "votes": 9000,
                "budget_category": "High",
                "online_order": False,
                "book_table": True,
            },
            {
                "name": "CTR - Shri Sagar",
                "location": "Malleshwaram",
                "cuisines": "South Indian",
                "cost_for_two": 200,
                "rating": 4.8,
                "votes": 8500,
                "budget_category": "Low",
                "online_order": True,
                "book_table": False,
            },
            {
                "name": "Empire Restaurant",
                "location": "Koramangala",
                "cuisines": "North Indian, Mughlai",
                "cost_for_two": 600,
                "rating": 4.1,
                "votes": 3200,
                "budget_category": "Medium",
                "online_order": True,
                "book_table": False,
            },
        ]
    )


# ── E1: All preference fields are empty ──────────────────────────────────────
def test_e1_all_preference_fields_empty(sample_dataset: pd.DataFrame) -> None:
    """E1: All preference fields empty -> Return top highest-rated restaurants globally."""
    filter_engine = FilterEngine()
    empty_prefs = UserPreferences()
    assert empty_prefs.is_empty() is True

    result = filter_engine.filter(sample_dataset, empty_prefs)
    assert len(result.filtered_df) > 0
    # Highest rated should be at the top
    top_row = result.filtered_df.iloc[0]
    assert top_row["name"] == "CTR - Shri Sagar"
    assert top_row["rating"] == 4.8


# ── E2: Location doesn't exist in dataset ────────────────────────────────────
def test_e2_location_does_not_exist(sample_dataset: pd.DataFrame) -> None:
    """E2: Location doesn't exist -> Relaxes location filter and returns results."""
    filter_engine = FilterEngine(min_results=2)
    prefs = UserPreferences(location="AtlantisUnderwaterCity", min_rating=4.0)

    result = filter_engine.filter(sample_dataset, prefs)
    assert "location" in result.relaxed_filters
    assert len(result.filtered_df) >= 2


# ── E3: Cuisine not in dataset ───────────────────────────────────────────────
def test_e3_cuisine_not_in_dataset(sample_dataset: pd.DataFrame) -> None:
    """E3: Cuisine not in dataset -> Relaxes cuisine filter and informs via relaxed_filters."""
    filter_engine = FilterEngine(min_results=2)
    prefs = UserPreferences(cuisine="MartianAlienFood", min_rating=4.0)

    result = filter_engine.filter(sample_dataset, prefs)
    assert "cuisine" in result.relaxed_filters
    assert len(result.filtered_df) >= 2


# ── E4: Min rating = 5.0 (no perfect matches) ────────────────────────────────
def test_e4_min_rating_5_no_perfect_matches(sample_dataset: pd.DataFrame) -> None:
    """E4: Min rating = 5.0 -> Relaxes rating filter to return closest high-rated matches."""
    filter_engine = FilterEngine(min_results=3)
    prefs = UserPreferences(min_rating=5.0)

    result = filter_engine.filter(sample_dataset, prefs)
    assert "min_rating" in result.relaxed_filters
    assert len(result.filtered_df) >= 3


# ── E5: Dataset has duplicate restaurants ───────────────────────────────────
def test_e5_duplicate_restaurants_deduplication() -> None:
    """E5: Dataset has duplicate entries -> Deduplicate on (name, location) during preprocessing."""
    raw_df = pd.DataFrame(
        [
            {
                "name": "Truffles",
                "location": "Koramangala",
                "rate": "4.6/5",
                "cuisines": "American",
                "approx_cost(for two people)": "800",
                "votes": "4000",
                "online_order": "Yes",
                "book_table": "No",
            },
            {
                "name": "Truffles",
                "location": "Koramangala",
                "rate": "4.2/5",  # Lower rating duplicate
                "cuisines": "American",
                "approx_cost(for two people)": "800",
                "votes": "1000",
                "online_order": "Yes",
                "book_table": "No",
            },
        ]
    )
    preprocessor = DataPreprocessor()
    clean_df = preprocessor.preprocess(raw_df)

    assert len(clean_df) == 1
    assert clean_df.iloc[0]["rating"] == 4.6
    assert clean_df.iloc[0]["votes"] == 4000


# ── E6: LLM returns non-JSON response ───────────────────────────────────────
def test_e6_llm_returns_non_json_response(sample_dataset: pd.DataFrame) -> None:
    """E6: LLM returns non-JSON response -> Fallback regex parser parses or generates fallback."""
    parser = ResponseParser()
    non_json_response = """
    Here are my top recommendations for you!
    1. Restaurant: Truffles
       Cuisine: American, Italian
       Rating: 4.6
       Estimated Cost: ₹800 for two
       Explanation: Known for superb burgers and lively ambiance.
    """
    recs = parser.parse(non_json_response, available_restaurants=sample_dataset)
    assert len(recs) >= 1
    assert recs[0].restaurant_name == "Truffles"
    assert recs[0].rating == 4.6

    # Test complete gibberish fallback
    gibberish = "Sorry, I am an AI and cannot process your query right now."
    empty_recs = parser.parse(gibberish, available_restaurants=sample_dataset)
    # Should safely return empty list without crashing, enabling engine fallback
    assert isinstance(empty_recs, list)


# ── E7: LLM hallucinates a restaurant not in dataset ────────────────────────
def test_e7_llm_hallucinates_restaurant_not_in_dataset(sample_dataset: pd.DataFrame) -> None:
    """E7: LLM hallucinates nonexistent restaurant -> Parser validates and drops hallucination."""
    parser = ResponseParser()
    hallucinated_response = """
    [
        {
            "restaurant_name": "Imaginary Floating Castle",
            "cuisine": "Mythical",
            "rating": 5.0,
            "estimated_cost": "₹9999",
            "explanation": "This restaurant does not exist in Bangalore."
        },
        {
            "restaurant_name": "Truffles",
            "cuisine": "American",
            "rating": 4.6,
            "estimated_cost": "₹800 for two",
            "explanation": "Genuine Bangalore restaurant."
        }
    ]
    """
    recs = parser.parse(hallucinated_response, available_restaurants=sample_dataset)
    # The hallucinated restaurant should be pruned
    assert len(recs) == 1
    assert recs[0].restaurant_name == "Truffles"


# ── E8: Groq API key is missing/invalid ─────────────────────────────────────
def test_e8_groq_api_key_missing_or_invalid() -> None:
    """E8: Groq API key missing -> Raises LLMAPIKeyError or falls back gracefully."""
    with patch.dict("os.environ", {"GROQ_API_KEY": ""}, clear=True):
        config = AppConfig(groq_api_key="")
        with pytest.raises(LLMAPIKeyError):
            client = LLMClient(api_key="", config=config)
            client.generate("Test prompt")


# ── E9: Network failure during dataset download ──────────────────────────────
def test_e9_network_failure_during_dataset_download(tmp_path: Path) -> None:
    """E9: Network failure during dataset download -> Falls back to cache or raises DatasetLoadError."""
    # When cache does not exist and network fails
    empty_cache_dir = tmp_path / "empty_cache"
    empty_cache_dir.mkdir()
    config = AppConfig(cache_dir=empty_cache_dir)
    loader = DatasetLoader(config=config)

    with patch("src.data.loader.load_dataset", side_effect=Exception("Connection timed out")):
        with pytest.raises(DatasetLoadError):
            loader.load(force_download=True)


# ── E10: Very long additional_prefs text ────────────────────────────────────
def test_e10_very_long_additional_prefs_truncated() -> None:
    """E10: Very long additional_prefs (5000+ chars) -> Truncates to 500 chars before prompt."""
    long_text = "outdoor seating and great coffee " * 200
    assert len(long_text) > 500

    prefs = UserPreferences(additional_prefs=long_text)
    assert len(prefs.additional_prefs) == 500

    # Ensure PromptBuilder safely handles truncated prefs without buffer blowout
    builder = PromptBuilder()
    df_sample = pd.DataFrame([{"name": "Toit", "location": "Indiranagar", "cuisines": "Pub", "rating": 4.7, "cost_for_two": 1500, "budget_category": "High"}])
    prompt = builder.build_recommendation_prompt(df_sample, prefs, top_n=1)
    assert len(prompt) < 10000
    assert "outdoor seating" in prompt
