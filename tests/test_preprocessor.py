"""
Unit tests for DataPreprocessor.
"""

import pandas as pd
import pytest

from src.data.preprocessor import DataPreprocessor
from src.utils.config import AppConfig


@pytest.fixture
def preprocessor() -> DataPreprocessor:
    """Fixture providing a standard DataPreprocessor."""
    config = AppConfig(budget_low_max=400, budget_medium_max=1000)
    return DataPreprocessor(config=config)


def test_preprocess_empty_dataframe(preprocessor: DataPreprocessor):
    """Verify empty DataFrame returns empty DataFrame with final columns."""
    df = pd.DataFrame()
    result = preprocessor.preprocess(df)
    assert result.empty
    assert list(result.columns) == preprocessor.FINAL_COLUMNS


def test_preprocess_drops_missing_or_empty_names(preprocessor: DataPreprocessor):
    """Verify rows with missing or whitespace-only names are dropped (PP-09)."""
    df = pd.DataFrame({
        "name": [None, "", "   ", "Valid Cafe"],
        "rate": ["4.0/5", "4.0/5", "4.0/5", "4.0/5"],
        "approx_cost(for two people)": ["500", "500", "500", "500"],
        "location": ["Koramangala", "Koramangala", "Koramangala", "Koramangala"],
        "cuisines": ["Cafe", "Cafe", "Cafe", "Cafe"],
    })
    result = preprocessor.preprocess(df)
    assert len(result) == 1
    assert result.iloc[0]["name"] == "Valid Cafe"


def test_preprocess_sanitizes_html_in_name(preprocessor: DataPreprocessor):
    """Verify HTML tags in restaurant names are stripped (PP-10)."""
    df = pd.DataFrame({
        "name": ["<b>Bistro</b> &amp; Grill <script>alert(1)</script>"],
        "rate": ["4.2/5"],
        "approx_cost(for two people)": ["600"],
        "location": ["Indiranagar"],
        "cuisines": ["Italian"],
    })
    result = preprocessor.preprocess(df)
    assert len(result) == 1
    assert "<" not in result.iloc[0]["name"]
    assert ">" not in result.iloc[0]["name"]
    assert "Bistro" in result.iloc[0]["name"]


def test_preprocess_drops_invalid_ratings(preprocessor: DataPreprocessor):
    """Verify rows with non-numeric or missing ratings are dropped (PP-01)."""
    df = pd.DataFrame({
        "name": ["R1", "R2", "R3", "R4", "R5"],
        "rate": ["NEW", "-", None, "", "4.1/5"],
        "approx_cost(for two people)": ["500", "500", "500", "500", "500"],
        "location": ["Koramangala"] * 5,
        "cuisines": ["North Indian"] * 5,
    })
    result = preprocessor.preprocess(df)
    assert len(result) == 1
    assert result.iloc[0]["name"] == "R5"
    assert result.iloc[0]["rating"] == 4.1


def test_preprocess_normalizes_and_clips_ratings(preprocessor: DataPreprocessor):
    """Verify ratings are parsed and clipped to [0.0, 5.0] (PP-02)."""
    df = pd.DataFrame({
        "name": ["R1", "R2", "R3", "R4"],
        "rate": ["4.5/5", "3.8 /5", "-1.5/5", "7.2/5"],
        "approx_cost(for two people)": ["500"] * 4,
        "location": ["Koramangala"] * 4,
        "cuisines": ["Italian"] * 4,
    })
    result = preprocessor.preprocess(df)
    ratings = dict(zip(result["name"], result["rating"]))

    assert ratings["R1"] == 4.5
    assert ratings["R2"] == 3.8
    assert ratings["R3"] == 0.0  # Clipped from negative
    assert ratings["R4"] == 5.0  # Clipped from > 5.0


def test_preprocess_cost_parsing_and_budget_categories(preprocessor: DataPreprocessor):
    """Verify cost extraction and categorization into Low, Medium, High, Unknown."""
    df = pd.DataFrame({
        "name": ["Street Stall", "Cafe", "Fine Dine", "No Cost", "Zero Cost"],
        "rate": ["4.0/5"] * 5,
        "approx_cost(for two people)": [
            "300",          # <= 400 -> Low
            "800",          # 401 - 1000 -> Medium
            "1,500",        # > 1000 -> High (string with comma)
            None,           # missing -> Unknown
            "0",            # 0 -> Unknown (PP-04)
        ],
        "location": ["Koramangala"] * 5,
        "cuisines": ["Street Food"] * 5,
    })
    result = preprocessor.preprocess(df)
    cats = dict(zip(result["name"], result["budget_category"]))

    assert cats["Street Stall"] == "Low"
    assert cats["Cafe"] == "Medium"
    assert cats["Fine Dine"] == "High"
    assert cats["No Cost"] == "Unknown"
    assert cats["Zero Cost"] == "Unknown"

    costs = dict(zip(result["name"], result["cost_for_two"]))
    assert costs["Street Stall"] == 300
    assert costs["Cafe"] == 800
    assert costs["Fine Dine"] == 1500


def test_preprocess_cleans_cuisines(preprocessor: DataPreprocessor):
    """Verify cuisines are stripped of whitespace and title-cased (PP-07)."""
    df = pd.DataFrame({
        "name": ["R1", "R2", "R3"],
        "rate": ["4.0/5"] * 3,
        "approx_cost(for two people)": ["500"] * 3,
        "location": ["Koramangala"] * 3,
        "cuisines": [
            "north indian,  chinese , fast food",
            None,
            "   ",
        ],
    })
    result = preprocessor.preprocess(df)
    cuisines = dict(zip(result["name"], result["cuisines"]))

    assert cuisines["R1"] == "North Indian, Chinese, Fast Food"
    assert cuisines["R2"] == "Unknown"
    assert cuisines["R3"] == "Unknown"


def test_preprocess_standardizes_location(preprocessor: DataPreprocessor):
    """Verify location whitespace is stripped and title-cased (PP-11)."""
    df = pd.DataFrame({
        "name": ["R1", "R2", "R3"],
        "rate": ["4.0/5"] * 3,
        "approx_cost(for two people)": ["500"] * 3,
        "location": ["  koramangala 5th block  ", None, "   "],
        "cuisines": ["Cafe"] * 3,
    })
    result = preprocessor.preprocess(df)
    locs = dict(zip(result["name"], result["location"]))

    assert locs["R1"] == "Koramangala 5Th Block"
    assert locs["R2"] == "Unknown"
    assert locs["R3"] == "Unknown"


def test_preprocess_votes_and_flags(preprocessor: DataPreprocessor):
    """Verify votes and online_order / book_table flags are normalized (PP-13, PP-14)."""
    df = pd.DataFrame({
        "name": ["R1", "R2"],
        "rate": ["4.0/5", "4.0/5"],
        "approx_cost(for two people)": ["500", "500"],
        "location": ["Koramangala", "Koramangala"],
        "cuisines": ["Cafe", "Cafe"],
        "votes": ["150", None],
        "online_order": ["yes", "0"],
        "book_table": ["TRUE", "no"],
    })
    result = preprocessor.preprocess(df)

    assert result.iloc[0]["votes"] == 150
    assert result.iloc[0]["online_order"] == "Yes"
    assert result.iloc[0]["book_table"] == "Yes"

    assert result.iloc[1]["votes"] == 0
    assert result.iloc[1]["online_order"] == "No"
    assert result.iloc[1]["book_table"] == "No"


def test_preprocess_deduplicates_restaurants(preprocessor: DataPreprocessor):
    """Verify duplicate restaurants by (name, location) keep the best rating & votes (DI-09)."""
    df = pd.DataFrame({
        "name": ["Empire Restaurant", "Empire Restaurant", "Empire Restaurant"],
        "location": ["Indiranagar", "Indiranagar", "Koramangala"],
        "rate": ["3.8/5", "4.4/5", "4.1/5"],
        "votes": [100, 500, 300],
        "approx_cost(for two people)": ["600", "600", "600"],
        "cuisines": ["North Indian", "North Indian", "North Indian"],
    })
    result = preprocessor.preprocess(df)

    # 3 inputs: 2 are (Empire Restaurant, Indiranagar), 1 is (Empire Restaurant, Koramangala)
    # Deduplication should yield 2 records.
    assert len(result) == 2

    # The Indiranagar entry should have the higher rating (4.4)
    indira_entry = result[result["location"] == "Indiranagar"].iloc[0]
    assert indira_entry["rating"] == 4.4
    assert indira_entry["votes"] == 500


def test_preprocess_column_selection_and_order(preprocessor: DataPreprocessor):
    """Verify final output DataFrame contains exact required columns in order."""
    df = pd.DataFrame({
        "name": ["Truffles"],
        "rate": ["4.5/5"],
        "approx_cost(for two people)": ["800"],
        "location": ["St. Marks Road"],
        "cuisines": ["American, Burger"],
        "votes": [2500],
        "online_order": ["Yes"],
        "book_table": ["No"],
        "url": ["https://zomato.com/truffles"],
        "phone": ["12345678"],
    })
    result = preprocessor.preprocess(df)

    assert list(result.columns) == [
        "name",
        "location",
        "cuisines",
        "cost_for_two",
        "rating",
        "votes",
        "budget_category",
        "online_order",
        "book_table",
    ]
    # Extra columns like url, phone should not be in the output
    assert "url" not in result.columns
    assert "phone" not in result.columns
