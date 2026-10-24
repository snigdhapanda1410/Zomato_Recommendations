"""
Unit tests for ResponseParser and Recommendation.
"""

import pandas as pd
import pytest

from src.filters.filter_engine import UserPreferences
from src.llm.response_parser import Recommendation, ResponseParser


@pytest.fixture
def parser() -> ResponseParser:
    return ResponseParser()


def test_parse_valid_json_array(parser: ResponseParser):
    """Verify parsing standard top-level JSON array."""
    raw = """
    [
      {
        "restaurant_name": "Truffles",
        "cuisine": "American, Italian",
        "rating": 4.5,
        "estimated_cost": "₹800 for two",
        "explanation": "Great burgers and pasta within medium budget."
      },
      {
        "restaurant_name": "Pasta Street",
        "cuisine": "Italian",
        "rating": 4.3,
        "estimated_cost": "₹600 for two",
        "explanation": "Authentic Italian dishes."
      }
    ]
    """
    recs = parser.parse(raw)
    assert len(recs) == 2
    assert recs[0].restaurant_name == "Truffles"
    assert recs[0].rating == 4.5
    assert recs[0].estimated_cost == "₹800 for two"
    assert "burgers" in recs[0].explanation


def test_parse_wrapped_json_object(parser: ResponseParser):
    """Verify parsing when LLM wraps output in a dictionary with recommendations key."""
    raw = """
    {
      "recommendations": [
        {
          "restaurant_name": "Toit",
          "cuisine": "American, Finger Food",
          "rating": 4.7,
          "estimated_cost": "₹1,500 for two",
          "explanation": "Famous craft brewery."
        }
      ]
    }
    """
    recs = parser.parse(raw)
    assert len(recs) == 1
    assert recs[0].restaurant_name == "Toit"
    assert recs[0].rating == 4.7


def test_parse_markdown_code_fences(parser: ResponseParser):
    """Verify markdown ```json ... ``` blocks are properly stripped."""
    raw = """```json
    [
      {
        "restaurant_name": "Corner House",
        "cuisine": "Desserts",
        "rating": 4.4,
        "estimated_cost": "₹300 for two",
        "explanation": "Best ice cream in town."
      }
    ]
    ```"""
    recs = parser.parse(raw)
    assert len(recs) == 1
    assert recs[0].restaurant_name == "Corner House"


def test_fallback_regex_parsing_malformed_json(parser: ResponseParser):
    """Verify regex fallback recovers recommendations from malformed text (E6)."""
    raw = """
    Here are the recommendations you requested:
    {
      "restaurant_name": "Truffles",
      "cuisine": "American",
      "rating": 4.5,
      "estimated_cost": "₹800",
      "explanation": "Top burger spot."
    }
    I hope you enjoy dining here!
    """
    recs = parser.parse(raw)
    assert len(recs) == 1
    assert recs[0].restaurant_name == "Truffles"
    assert recs[0].rating == 4.5


def test_hallucination_filtering(parser: ResponseParser):
    """Verify restaurants not in available list are filtered out (E7, LLM-06)."""
    raw = """
    [
      {
        "restaurant_name": "Truffles",
        "cuisine": "American",
        "rating": 4.5,
        "estimated_cost": "₹800 for two",
        "explanation": "Real restaurant."
      },
      {
        "restaurant_name": "Hallucinated Bistro 99",
        "cuisine": "French",
        "rating": 4.9,
        "estimated_cost": "₹2,000 for two",
        "explanation": "Does not exist in dataset."
      }
    ]
    """
    allowed_restaurants = ["Truffles", "Pasta Street", "Toit"]
    recs = parser.parse(raw, available_restaurants=allowed_restaurants)

    assert len(recs) == 1
    assert recs[0].restaurant_name == "Truffles"


def test_rating_normalization_from_string(parser: ResponseParser):
    """Verify rating formats like '4.2/5' are converted to float 4.2."""
    raw = """
    [
      {
        "restaurant_name": "Sunny's",
        "cuisine": "Italian",
        "rating": "4.2/5",
        "estimated_cost": 1200,
        "explanation": "Fine dining."
      }
    ]
    """
    recs = parser.parse(raw)
    assert len(recs) == 1
    assert recs[0].rating == 4.2
    assert "₹1200 for two" in recs[0].estimated_cost


def test_parse_empty_or_whitespace_returns_empty(parser: ResponseParser):
    """Verify empty string returns empty list without error."""
    assert parser.parse("") == []
    assert parser.parse("   ") == []


def test_generate_fallback_recommendations(parser: ResponseParser):
    """Verify offline fallback produces structured recommendations (Task 4.8)."""
    df = pd.DataFrame({
        "name": ["Truffles", "Toit"],
        "location": ["Koramangala", "Indiranagar"],
        "cuisines": ["American", "Finger Food"],
        "budget_category": ["Medium", "High"],
        "cost_for_two": [800, 1500],
        "rating": [4.5, 4.7],
        "votes": [3500, 5000],
    })
    prefs = UserPreferences(cuisine="American", budget="Medium")
    recs = parser.generate_fallback(df, prefs, top_n=2)

    assert len(recs) == 2
    # Toit has higher rating/votes so it should be first
    assert recs[0].restaurant_name == "Toit"
    assert recs[0].rating == 4.7
    assert all(r.explanation for r in recs)
    assert all("for two" in r.estimated_cost for r in recs)
