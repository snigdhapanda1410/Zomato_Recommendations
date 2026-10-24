"""
Unit and integration tests for RecommendationEngine and RecommendationResult.
"""

from unittest.mock import MagicMock, patch
import pandas as pd
import pytest

from src.filters.filter_engine import FilterEngine, FilterResult, UserPreferences
from src.llm.llm_client import LLMClient, LLMError
from src.llm.prompt_builder import PromptBuilder
from src.llm.response_parser import Recommendation, ResponseParser
from src.recommendation.engine import RecommendationEngine, RecommendationResult
from src.utils.config import AppConfig


@pytest.fixture
def sample_clean_df() -> pd.DataFrame:
    """Provide a minimal preprocessed DataFrame for testing."""
    return pd.DataFrame(
        [
            {
                "name": "Truffles",
                "location": "Koramangala",
                "cuisines": "American, Italian, Desserts",
                "cost_for_two": 800,
                "rating": 4.6,
                "votes": 4500,
                "budget_category": "Medium",
                "online_order": True,
                "book_table": False,
            },
            {
                "name": "Pasta Street",
                "location": "Koramangala",
                "cuisines": "Italian, Continental",
                "cost_for_two": 900,
                "rating": 4.4,
                "votes": 1200,
                "budget_category": "Medium",
                "online_order": True,
                "book_table": True,
            },
            {
                "name": "Chianti",
                "location": "Indiranagar",
                "cuisines": "Italian, European",
                "cost_for_two": 1500,
                "rating": 4.5,
                "votes": 2200,
                "budget_category": "High",
                "online_order": False,
                "book_table": True,
            },
            {
                "name": "Corner House Ice Cream",
                "location": "Koramangala",
                "cuisines": "Ice Cream, Desserts",
                "cost_for_two": 300,
                "rating": 4.7,
                "votes": 3500,
                "budget_category": "Low",
                "online_order": True,
                "book_table": False,
            },
        ]
    )


def test_recommendation_result_dunder_methods() -> None:
    """Test iteration, length, and indexing of RecommendationResult."""
    recs = [
        Recommendation(
            restaurant_name="Truffles",
            cuisine="American",
            rating=4.5,
            estimated_cost="₹800",
            explanation="Great burger spot",
        ),
        Recommendation(
            restaurant_name="Pasta Street",
            cuisine="Italian",
            rating=4.4,
            estimated_cost="₹900",
            explanation="Tasty pasta",
        ),
    ]
    res = RecommendationResult(
        recommendations=recs,
        total_matches=2,
        filters_applied={"location": "Koramangala"},
        filters_relaxed=[],
    )

    assert len(res) == 2
    assert res[0].restaurant_name == "Truffles"
    assert res[1].restaurant_name == "Pasta Street"
    names = [r.restaurant_name for r in res]
    assert names == ["Truffles", "Pasta Street"]


def test_recommendation_engine_initialization(sample_clean_df: pd.DataFrame) -> None:
    """Test initialization and preprocessed data retrieval."""
    engine = RecommendationEngine(preprocessed_df=sample_clean_df)
    df = engine.get_preprocessed_data()

    assert len(df) == 4
    locations = engine.get_available_locations()
    assert "Indiranagar" in locations
    assert "Koramangala" in locations

    cuisines = engine.get_available_cuisines()
    assert "Italian" in cuisines
    assert "Desserts" in cuisines


def test_recommendation_engine_from_config() -> None:
    """Test factory method construction."""
    config = AppConfig()
    engine = RecommendationEngine.from_config(config)
    assert engine.config is not None
    assert isinstance(engine.loader, object)
    assert isinstance(engine.filter_engine, FilterEngine)


def test_recommendation_engine_recommend_mock_llm(sample_clean_df: pd.DataFrame) -> None:
    """Test recommendation pipeline with a mocked LLM client."""
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.generate.return_value = """
    [
        {
            "restaurant_name": "Truffles",
            "cuisine": "American, Italian",
            "rating": 4.6,
            "estimated_cost": "₹800 for two",
            "explanation": "Perfect match for your Italian preference with high ratings."
        }
    ]
    """

    engine = RecommendationEngine(
        preprocessed_df=sample_clean_df,
        llm_client=mock_llm,
    )

    prefs = UserPreferences(location="Koramangala", cuisine="Italian", min_rating=4.0)
    result = engine.recommend(prefs, top_n=1)

    assert isinstance(result, RecommendationResult)
    assert len(result) == 1
    assert result[0].restaurant_name == "Truffles"
    assert result.is_fallback is False
    assert result.filters_applied["location"] == "Koramangala"
    assert result.filters_applied["cuisine"] == "Italian"


def test_recommendation_engine_fallback_on_llm_error(sample_clean_df: pd.DataFrame) -> None:
    """Test recommendation pipeline falls back to rule-based ranking if LLM errors."""
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.generate.side_effect = LLMError("API rate limit exceeded")

    engine = RecommendationEngine(
        preprocessed_df=sample_clean_df,
        llm_client=mock_llm,
    )

    prefs = UserPreferences(location="Koramangala")
    result = engine.recommend(prefs, top_n=2)

    assert isinstance(result, RecommendationResult)
    assert result.is_fallback is True
    assert "API rate limit exceeded" in str(result.fallback_reason)
    assert len(result) >= 1
    # Fallback should return valid recommendations from the dataset
    assert result[0].restaurant_name in ["Corner House Ice Cream", "Truffles", "Pasta Street"]


def test_recommendation_engine_fallback_on_empty_filter_results() -> None:
    """Test fallback when 0 restaurants match in an empty DataFrame."""
    empty_df = pd.DataFrame(columns=["name", "location", "cuisines", "rating", "cost_for_two", "votes"])
    engine = RecommendationEngine(preprocessed_df=empty_df)

    prefs = UserPreferences(location="NonexistentArea")
    result = engine.recommend(prefs, top_n=3)

    assert result.is_fallback is True
    assert result.total_matches == 0
    assert len(result) == 0
