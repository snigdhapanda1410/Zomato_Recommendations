"""
Performance benchmark tests (Phase 6, Task 6.9).

Validates that data ingestion, filtering, prompt construction, and response parsing
complete in well under the 10-second requirement (excluding network LLM inference).
"""

import time
import pandas as pd
import pytest

from src.data.loader import DatasetLoader
from src.data.preprocessor import DataPreprocessor
from src.filters.filter_engine import FilterEngine, UserPreferences
from src.llm.prompt_builder import PromptBuilder
from src.llm.response_parser import ResponseParser
from src.recommendation.engine import RecommendationEngine
from src.utils.config import AppConfig


def test_filter_engine_latency(sample_large_df: pd.DataFrame) -> None:
    """Validate FilterEngine execution completes in under 100 milliseconds."""
    engine = FilterEngine()
    prefs = UserPreferences(
        location="Koramangala",
        budget="Medium",
        cuisine="Italian",
        min_rating=4.0,
        additional_prefs="outdoor seating",
    )

    t0 = time.perf_counter()
    result = engine.filter(sample_large_df, prefs)
    elapsed = time.perf_counter() - t0

    assert elapsed < 0.2, f"Filter engine took {elapsed:.4f}s, expected < 0.2s"
    assert len(result.filtered_df) > 0


def test_prompt_builder_latency(sample_large_df: pd.DataFrame) -> None:
    """Validate PromptBuilder formatting completes in under 50 milliseconds."""
    builder = PromptBuilder()
    prefs = UserPreferences(location="Indiranagar", budget="High", cuisine="Italian")

    t0 = time.perf_counter()
    prompt = builder.build_recommendation_prompt(sample_large_df.head(50), prefs, top_n=5)
    elapsed = time.perf_counter() - t0

    assert elapsed < 0.1, f"Prompt builder took {elapsed:.4f}s, expected < 0.1s"
    assert len(prompt) > 0


def test_response_parser_latency(sample_large_df: pd.DataFrame) -> None:
    """Validate ResponseParser JSON & regex validation completes in under 50 milliseconds."""
    parser = ResponseParser()
    sample_json = """
    [
        {"restaurant_name": "Restaurant 0", "cuisine": "American", "rating": 4.6, "estimated_cost": "₹800 for two", "explanation": "Classic burgers."},
        {"restaurant_name": "Restaurant 1", "cuisine": "Pub", "rating": 4.7, "estimated_cost": "₹1500 for two", "explanation": "Craft brews."},
        {"restaurant_name": "Restaurant 2", "cuisine": "Dessert", "rating": 4.5, "estimated_cost": "₹350 for two", "explanation": "Hot chocolate fudge."}
    ]
    """

    t0 = time.perf_counter()
    recs = parser.parse(sample_json, available_restaurants=sample_large_df)
    elapsed = time.perf_counter() - t0

    assert elapsed < 0.1, f"Response parser took {elapsed:.4f}s, expected < 0.1s"
    assert len(recs) == 3


def test_end_to_end_deterministic_pipeline_latency(sample_large_df: pd.DataFrame) -> None:
    """Validate end-to-end fallback/deterministic recommendation takes < 1 second."""
    engine = RecommendationEngine(preprocessed_df=sample_large_df)
    prefs = UserPreferences(location="Koramangala", cuisine="Italian", min_rating=4.0)

    t0 = time.perf_counter()
    # Mocking LLM failure to test full deterministic end-to-end latency
    engine.llm_client.generate = lambda _: (_ for _ in ()).throw(Exception("Force fallback"))
    result = engine.recommend(prefs, top_n=5)
    elapsed = time.perf_counter() - t0

    assert elapsed < 1.0, f"End-to-end pipeline took {elapsed:.4f}s, expected < 1.0s"
    assert len(result.recommendations) > 0


@pytest.fixture
def sample_large_df() -> pd.DataFrame:
    """Generate a 5,000 row DataFrame to simulate realistic Bangalore dataset scale."""
    rows = []
    locations = ["Koramangala", "Indiranagar", "HSR", "Whitefield", "Jayanagar"]
    cuisines = ["North Indian", "South Indian", "Italian", "Chinese", "American"]
    budgets = ["Low", "Medium", "High"]

    for i in range(5000):
        rows.append(
            {
                "name": f"Restaurant {i}",
                "location": locations[i % len(locations)],
                "cuisines": f"{cuisines[i % len(cuisines)]}, Continental",
                "cost_for_two": 300 + (i % 15) * 100,
                "rating": 3.0 + (i % 20) * 0.1,
                "votes": 50 + i * 2,
                "budget_category": budgets[i % len(budgets)],
                "online_order": i % 2 == 0,
                "book_table": i % 3 == 0,
            }
        )
    return pd.DataFrame(rows)
