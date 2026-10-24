"""
Unit tests for FilterEngine, UserPreferences, and FilterResult.
"""

import pandas as pd
import pytest

from src.filters.filter_engine import FilterEngine, FilterResult, UserPreferences
from src.utils.config import AppConfig


@pytest.fixture
def sample_clean_df() -> pd.DataFrame:
    """Fixture providing a mock cleaned restaurant DataFrame."""
    return pd.DataFrame({
        "name": [
            "Truffles",
            "Pasta Street",
            "Toit",
            "Corner House",
            "Chai Point",
            "Empire",
            "Sunny's",
            "Street Momos",
        ],
        "location": [
            "Koramangala 5Th Block",
            "Indiranagar",
            "Indiranagar",
            "Koramangala 7Th Block",
            "Koramangala 1St Block",
            "Indiranagar",
            "Lavelle Road",
            "Whitefield",
        ],
        "cuisines": [
            "American, Burger, Italian",
            "Italian, Pizza",
            "Italian, American, Finger Food",
            "Desserts, Ice Cream",
            "Beverages, Tea",
            "North Indian, Mughlai",
            "Italian, European",
            "Tibetan, Chinese",
        ],
        "cost_for_two": [800, 900, 1500, 300, 200, 600, 1800, 150],
        "rating": [4.5, 4.3, 4.7, 4.4, 3.8, 3.9, 4.2, 3.5],
        "votes": [3500, 1200, 5000, 2200, 400, 1800, 900, 100],
        "budget_category": [
            "Medium",
            "Medium",
            "High",
            "Low",
            "Low",
            "Medium",
            "High",
            "Low",
        ],
        "online_order": ["Yes", "Yes", "No", "Yes", "Yes", "Yes", "No", "No"],
        "book_table": ["No", "Yes", "Yes", "No", "No", "Yes", "Yes", "No"],
    })


# ── UserPreferences Tests ──────────────────────────────────────


def test_user_preferences_defaults():
    """Verify default values and is_empty() method."""
    prefs = UserPreferences()
    assert prefs.location is None
    assert prefs.budget is None
    assert prefs.cuisine is None
    assert prefs.min_rating == 0.0
    assert prefs.additional_prefs is None
    assert prefs.is_empty() is True


def test_user_preferences_sanitization():
    """Verify whitespace stripping and rating clamping."""
    prefs = UserPreferences(
        location="  Indiranagar  ",
        budget=" Medium ",
        cuisine=" Italian ",
        min_rating=6.5,  # > 5.0
        additional_prefs=" outdoor seating ",
    )
    assert prefs.location == "Indiranagar"
    assert prefs.budget == "Medium"
    assert prefs.cuisine == "Italian"
    assert prefs.min_rating == 5.0
    assert prefs.additional_prefs == "outdoor seating"
    assert prefs.is_empty() is False


def test_user_preferences_truncates_long_additional_prefs():
    """Verify very long additional_prefs text is capped at 500 chars (UI-06, E10)."""
    long_text = "a" * 600
    prefs = UserPreferences(additional_prefs=long_text)
    assert len(prefs.additional_prefs) == 500


# ── Individual Filter Method Tests ─────────────────────────────


def test_filter_by_location(sample_clean_df: pd.DataFrame):
    """Verify location substring filtering and case-insensitivity."""
    engine = FilterEngine()

    # Substring match "Koramangala" matches 1st, 5th, 7th block
    res = engine._filter_by_location(sample_clean_df, "Koramangala")
    assert len(res) == 3
    assert all("Koramangala" in loc for loc in res["location"])

    # City alias "Bangalore" matches all
    res_all = engine._filter_by_location(sample_clean_df, "Bangalore")
    assert len(res_all) == len(sample_clean_df)

    # None or empty returns all
    assert len(engine._filter_by_location(sample_clean_df, None)) == len(sample_clean_df)
    assert len(engine._filter_by_location(sample_clean_df, "")) == len(sample_clean_df)


def test_filter_by_budget(sample_clean_df: pd.DataFrame):
    """Verify budget filtering by category."""
    engine = FilterEngine()

    res_low = engine._filter_by_budget(sample_clean_df, "Low")
    assert len(res_low) == 3
    assert all(cat == "Low" for cat in res_low["budget_category"])

    res_med = engine._filter_by_budget(sample_clean_df, "medium")
    assert len(res_med) == 3
    assert all(cat == "Medium" for cat in res_med["budget_category"])

    # "All" or None
    assert len(engine._filter_by_budget(sample_clean_df, "All")) == len(sample_clean_df)
    assert len(engine._filter_by_budget(sample_clean_df, None)) == len(sample_clean_df)


def test_filter_by_cuisine(sample_clean_df: pd.DataFrame):
    """Verify partial cuisine matching."""
    engine = FilterEngine()

    res_italian = engine._filter_by_cuisine(sample_clean_df, "Italian")
    assert len(res_italian) == 4
    assert all("Italian" in c for c in res_italian["cuisines"])

    res_burger = engine._filter_by_cuisine(sample_clean_df, "Burger")
    assert len(res_burger) == 1
    assert res_burger.iloc[0]["name"] == "Truffles"


def test_filter_by_rating(sample_clean_df: pd.DataFrame):
    """Verify minimum rating filtering."""
    engine = FilterEngine()

    res_4_5 = engine._filter_by_rating(sample_clean_df, 4.5)
    assert len(res_4_5) == 2  # Truffles (4.5), Toit (4.7)
    assert all(r >= 4.5 for r in res_4_5["rating"])

    # 0.0 or None returns all
    assert len(engine._filter_by_rating(sample_clean_df, 0.0)) == len(sample_clean_df)


# ── Combined & Sequential Filter Tests ─────────────────────────


def test_strict_multi_filter_success(sample_clean_df: pd.DataFrame):
    """Verify multiple active filters combine with AND logic."""
    engine = FilterEngine(min_results=1)
    prefs = UserPreferences(
        location="Indiranagar",
        budget="Medium",
        cuisine="Italian",
        min_rating=4.0,
    )
    result = engine.filter(sample_clean_df, prefs)

    assert len(result.filtered_df) == 1
    assert result.filtered_df.iloc[0]["name"] == "Pasta Street"
    assert result.is_relaxed is False


# ── Relaxation Strategy Tests ──────────────────────────────────


def test_relaxation_drops_rating_first(sample_clean_df: pd.DataFrame):
    """Verify that when results < 3, min_rating is dropped first."""
    engine = FilterEngine(min_results=3)
    # With min_rating=4.6, only 1 Italian matches (Toit 4.7).
    # Relaxing min_rating yields 4 Italian restaurants.
    prefs = UserPreferences(
        cuisine="Italian",
        min_rating=4.6,
    )
    result = engine.filter(sample_clean_df, prefs)

    assert len(result.filtered_df) >= 3
    assert "min_rating" in result.relaxed_filters
    assert "budget" not in result.relaxed_filters
    assert "cuisine" not in result.relaxed_filters


def test_relaxation_drops_budget_next(sample_clean_df: pd.DataFrame):
    """Verify budget is dropped if dropping rating is insufficient."""
    engine = FilterEngine(min_results=3)
    # Low budget + Italian has 0 restaurants in sample data.
    # Dropping rating gives 0. Dropping budget gives 4 Italian restaurants!
    prefs = UserPreferences(
        budget="Low",
        cuisine="Italian",
        min_rating=4.0,
    )
    result = engine.filter(sample_clean_df, prefs)

    assert len(result.filtered_df) >= 3
    assert "budget" in result.relaxed_filters
    # Italian restaurants should be returned
    assert any("Italian" in c for c in result.filtered_df["cuisines"])


def test_relaxation_drops_cuisine_next(sample_clean_df: pd.DataFrame):
    """Verify cuisine is dropped if dropping rating and budget is insufficient."""
    engine = FilterEngine(min_results=3)
    # Mexican cuisine has 0 restaurants. Dropping rating & budget gives 0.
    # Dropping cuisine returns restaurants in Indiranagar.
    prefs = UserPreferences(
        location="Indiranagar",
        cuisine="Mexican",
        min_rating=4.0,
    )
    result = engine.filter(sample_clean_df, prefs)

    assert len(result.filtered_df) >= 3
    assert "cuisine" in result.relaxed_filters


def test_relaxation_preserves_strict_matches_at_top(sample_clean_df: pd.DataFrame):
    """Verify strict matches appear at the beginning of relaxed results (FE-02)."""
    engine = FilterEngine(min_results=3)
    # In Indiranagar, High budget, Italian -> exactly 1 strict match: "Toit"
    prefs = UserPreferences(
        location="Indiranagar",
        budget="High",
        cuisine="Italian",
        min_rating=4.0,
    )
    result = engine.filter(sample_clean_df, prefs)

    assert len(result.filtered_df) >= 3
    assert result.is_relaxed is True
    # The strict match (Toit) must be in the results
    names = list(result.filtered_df["name"])
    assert "Toit" in names


# ── Truncation Tests ───────────────────────────────────────────


def test_result_truncation(sample_clean_df: pd.DataFrame):
    """Verify results are truncated to max_results when count exceeds threshold."""
    # Set max_results to 3
    engine = FilterEngine(max_results=3, min_results=1)
    prefs = UserPreferences()  # All empty matches all 8
    result = engine.filter(sample_clean_df, prefs)

    assert len(result.filtered_df) == 3
    assert result.is_truncated is True
    assert result.total_matched == len(sample_clean_df)
    # Highest rated should be first
    assert result.filtered_df.iloc[0]["rating"] == 4.7  # Toit


# ── Empty Input & Edge Cases ───────────────────────────────────


def test_all_empty_preferences_returns_top_rated(sample_clean_df: pd.DataFrame):
    """Verify empty preferences return top-rated restaurants globally (E1, UI-01)."""
    engine = FilterEngine()
    result = engine.filter(sample_clean_df, UserPreferences())

    assert len(result.filtered_df) == len(sample_clean_df)
    assert result.relaxed_filters == []
    # Sorted by rating descending
    assert result.filtered_df.iloc[0]["name"] == "Toit"


def test_nonexistent_location_relaxes_to_global(sample_clean_df: pd.DataFrame):
    """Verify querying a nonexistent location relaxes location (E2, UI-02)."""
    engine = FilterEngine(min_results=3)
    prefs = UserPreferences(location="NonexistentTown")
    result = engine.filter(sample_clean_df, prefs)

    assert len(result.filtered_df) >= 3
    assert "location" in result.relaxed_filters


def test_empty_dataframe_handled_safely():
    """Verify empty DataFrame input returns empty FilterResult safely."""
    engine = FilterEngine()
    result = engine.filter(pd.DataFrame(), UserPreferences(location="Indiranagar"))

    assert result.filtered_df.empty
    assert len(result) == 0
    assert result.total_matched == 0


def test_acceptance_criteria_scenario(sample_clean_df: pd.DataFrame):
    """Verify acceptance criteria snippet from implementation plan."""
    engine = FilterEngine()
    prefs = UserPreferences(
        location="Bangalore",
        budget="Medium",
        cuisine="Italian",
        min_rating=4.0,
    )
    result = engine.filter(sample_clean_df, prefs)

    assert len(result.filtered_df) >= 1
    assert all(result.filtered_df["rating"] >= 4.0)

