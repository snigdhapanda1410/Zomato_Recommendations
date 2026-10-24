"""
Unit tests for PromptBuilder.
"""

import pandas as pd
import pytest

from src.filters.filter_engine import UserPreferences
from src.llm.prompt_builder import PromptBuilder


@pytest.fixture
def sample_candidate_df() -> pd.DataFrame:
    """Fixture providing candidate restaurants for prompt testing."""
    return pd.DataFrame({
        "name": ["Truffles", "Pasta Street"],
        "location": ["Koramangala 5Th Block", "Indiranagar"],
        "cuisines": ["American, Burger", "Italian, Pizza"],
        "budget_category": ["Medium", "Medium"],
        "cost_for_two": [800, 600],
        "rating": [4.5, 4.3],
        "votes": [3500, 1200],
    })


def test_build_prompt_full_preferences(sample_candidate_df: pd.DataFrame):
    """Verify prompt incorporates all user preference fields."""
    builder = PromptBuilder()
    prefs = UserPreferences(
        location="Koramangala",
        budget="Medium",
        cuisine="Italian",
        min_rating=4.0,
        additional_prefs="outdoor seating, romantic vibe",
    )
    prompt = builder.build_recommendation_prompt(sample_candidate_df, prefs, top_n=3)

    assert "## USER PREFERENCES" in prompt
    assert "Location: Koramangala" in prompt
    assert "Budget: Medium" in prompt
    assert "Preferred Cuisine: Italian" in prompt
    assert "Minimum Rating: 4.0/5" in prompt
    assert "outdoor seating, romantic vibe" in prompt
    assert "top 3 that BEST match" in prompt
    assert "Truffles" in prompt
    assert "Pasta Street" in prompt
    assert "## OUTPUT FORMAT" in prompt


def test_build_prompt_empty_preferences(sample_candidate_df: pd.DataFrame):
    """Verify prompt handles empty preferences gracefully."""
    builder = PromptBuilder()
    prompt = builder.build_recommendation_prompt(sample_candidate_df, UserPreferences(), top_n=5)

    assert "Location: Any" in prompt
    assert "Budget: Any" in prompt
    assert "Preferred Cuisine: Any" in prompt
    assert "Minimum Rating: None" in prompt
    assert "top 5 that BEST match" in prompt


def test_build_prompt_sanitizes_braces(sample_candidate_df: pd.DataFrame):
    """Verify braces in preferences do not break prompt templating."""
    builder = PromptBuilder()
    prefs = UserPreferences(
        location="Bangalore {south}",
        additional_prefs="likes {quiet} corners",
    )
    prompt = builder.build_recommendation_prompt(sample_candidate_df, prefs, top_n=2)

    assert "Bangalore (south)" in prompt
    assert "likes (quiet) corners" in prompt


def test_format_restaurant_table_empty():
    """Verify empty DataFrame returns placeholder text."""
    builder = PromptBuilder()
    table_str = builder._format_restaurant_table(pd.DataFrame())
    assert "No restaurants currently available" in table_str
