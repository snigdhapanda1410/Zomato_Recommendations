"""
Response parser for LLM recommendation outputs.

Parses JSON responses, handles markdown wrappers, executes fallback regex parsing
when JSON is malformed, and validates groundedness against candidate datasets.
"""

from dataclasses import dataclass
import json
import re
from typing import Any
import pandas as pd

from src.filters.filter_engine import UserPreferences
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Recommendation:
    """
    Structured recommendation for a restaurant.

    Fields:
        restaurant_name: Name of the restaurant.
        cuisine: Types of cuisine offered.
        rating: Restaurant rating (0.0 to 5.0).
        estimated_cost: Approximate cost for two (e.g., '₹800 for two').
        explanation: Personalized justification explaining why it matches user preferences.
    """

    restaurant_name: str
    cuisine: str
    rating: float
    estimated_cost: str
    explanation: str


class ResponseParser:
    """
    Parses, validates, and normalizes LLM outputs into Recommendation objects.

    Features:
    - Markdown code block stripping (```json ... ```).
    - Top-level JSON array and wrapped JSON object handling.
    - Fallback regex parsing for malformed or truncated responses (E6).
    - Hallucination detection against candidate restaurant names (E7, LLM-06).
    - Offline / API-down fallback generator (Task 4.8).
    """

    def parse(
        self,
        raw_response: str,
        available_restaurants: list[str] | pd.DataFrame | None = None,
    ) -> list[Recommendation]:
        """
        Parse raw LLM response text into a list of Recommendation objects.

        Args:
            raw_response: Text returned by LLM.
            available_restaurants: Optional list of valid restaurant names or DataFrame
                                   used for hallucination validation.

        Returns:
            list[Recommendation]: Parsed and validated recommendations.
        """
        if not raw_response or not raw_response.strip():
            logger.warning("Empty response provided to ResponseParser.")
            return []

        # 1. Clean response text (strip markdown code blocks)
        cleaned = self._clean_raw_text(raw_response)

        # 2. Attempt standard JSON parsing
        data: Any = None
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.warning(
                f"Standard JSON decode failed ({exc}). Attempting fallback regex parsing..."
            )
            data = self._fallback_parse(raw_response)

        # 3. Extract items list if response was wrapped in an object
        items = self._extract_items_list(data)

        # 4. Validate and construct Recommendation objects
        valid_names = self._extract_valid_names(available_restaurants)
        recommendations = self._validate_and_build(items, valid_names)

        logger.info(f"Successfully parsed {len(recommendations)} recommendations.")
        return recommendations

    def _clean_raw_text(self, text: str) -> str:
        """Strip markdown fences and leading/trailing whitespace."""
        cleaned = text.strip()
        # Remove ```json ... ``` or ``` ... ```
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        return cleaned.strip()

    def _extract_items_list(self, data: Any) -> list[dict]:
        """Normalize parsed JSON into a list of dictionaries."""
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]

        if isinstance(data, dict):
            # Check common wrapper keys
            for key in ("recommendations", "restaurants", "results", "data", "items"):
                if key in data and isinstance(data[key], list):
                    return [item for item in data[key] if isinstance(item, dict)]

            # Check if dict itself represents a single recommendation object
            if "restaurant_name" in data or "name" in data:
                return [data]

        return []

    def _fallback_parse(self, text: str) -> list[dict]:
        """
        Extract JSON objects using regular expressions when full JSON parse fails.
        """
        results: list[dict] = []

        # 1. Look for array brackets: [ ... ]
        array_match = re.search(r"\[\s*(\{.*?\})\s*\]", text, re.DOTALL)
        if array_match:
            try:
                candidate = json.loads(array_match.group(0))
                if isinstance(candidate, list):
                    return candidate
            except json.JSONDecodeError:
                pass

        # 2. Extract individual { ... } objects
        object_patterns = re.findall(r"\{[^{}]*\}", text, re.DOTALL)
        for obj_str in object_patterns:
            try:
                parsed_obj = json.loads(obj_str)
                if isinstance(parsed_obj, dict) and (
                    "restaurant_name" in parsed_obj or "name" in parsed_obj
                ):
                    results.append(parsed_obj)
            except json.JSONDecodeError:
                continue

        if results:
            return results

        # 3. Plain text key-value extraction for non-JSON responses (RP-04, E6)
        blocks = re.split(
            r"(?:^|\n)\s*(?:\d+[\.\)]|\*|-)?\s*(?:Restaurant|Name):\s*",
            text,
            flags=re.IGNORECASE,
        )
        for block in blocks[1:]:
            lines = [l.strip() for l in block.strip().split("\n") if l.strip()]
            if not lines:
                continue
            name_candidate = lines[0].strip()
            obj: dict[str, Any] = {"restaurant_name": name_candidate}

            cuisine_match = re.search(r"Cuisine:\s*([^\n]+)", block, re.IGNORECASE)
            if cuisine_match:
                obj["cuisine"] = cuisine_match.group(1).strip()

            rating_match = re.search(r"Rating:\s*([0-9.]+)", block, re.IGNORECASE)
            if rating_match:
                try:
                    obj["rating"] = float(rating_match.group(1))
                except ValueError:
                    pass

            cost_match = re.search(r"(?:Estimated\s*)?Cost:\s*([^\n]+)", block, re.IGNORECASE)
            if cost_match:
                obj["estimated_cost"] = cost_match.group(1).strip()

            exp_match = re.search(r"Explanation:\s*([^\n]+)", block, re.IGNORECASE)
            if exp_match:
                obj["explanation"] = exp_match.group(1).strip()

            results.append(obj)

        return results

    def _extract_valid_names(
        self, available_restaurants: list[str] | pd.DataFrame | None
    ) -> set[str] | None:
        """Extract a lowercase set of valid restaurant names for hallucination checks."""
        if available_restaurants is None:
            return None

        if isinstance(available_restaurants, pd.DataFrame):
            col = "name" if "name" in available_restaurants.columns else "restaurant_name"
            if col in available_restaurants.columns:
                return {
                    str(n).strip().lower()
                    for n in available_restaurants[col].dropna()
                }
            return None

        if isinstance(available_restaurants, (list, tuple, set)):
            return {str(n).strip().lower() for n in available_restaurants}

        return None

    def _validate_and_build(
        self,
        items: list[dict],
        valid_names: set[str] | None = None,
    ) -> list[Recommendation]:
        """Validate fields and construct Recommendation instances."""
        recommendations: list[Recommendation] = []
        seen_names: set[str] = set()

        for item in items:
            name = item.get("restaurant_name") or item.get("name")
            if not name or not str(name).strip():
                continue

            clean_name = str(name).strip()
            name_lower = clean_name.lower()

            # Prevent duplicate recommendations
            if name_lower in seen_names:
                continue

            # Grounding check: verify name exists in dataset if valid_names provided (E7)
            if valid_names is not None and name_lower not in valid_names:
                # Try substring match before rejecting
                matched = any(
                    name_lower in v or v in name_lower for v in valid_names
                )
                if not matched:
                    logger.warning(
                        f"Filtered out hallucinated restaurant name not in dataset: '{clean_name}'"
                    )
                    continue

            # Cuisine
            cuisine = str(item.get("cuisine") or item.get("cuisines") or "Multi-Cuisine").strip()

            # Rating
            raw_rating = item.get("rating", 4.0)
            try:
                if isinstance(raw_rating, str) and "/5" in raw_rating:
                    raw_rating = raw_rating.split("/5")[0].strip()
                rating = float(raw_rating)
                rating = max(0.0, min(5.0, rating))
            except (ValueError, TypeError):
                rating = 4.0

            # Estimated cost
            raw_cost = item.get("estimated_cost") or item.get("cost_for_two") or item.get("cost")
            if not raw_cost:
                cost_str = "₹800 for two"
            elif isinstance(raw_cost, (int, float)):
                cost_str = f"₹{int(raw_cost)} for two"
            else:
                cost_str = str(raw_cost).strip()
                if not cost_str.startswith("₹") and any(c.isdigit() for c in cost_str):
                    cost_str = f"₹{cost_str}"
                if "for two" not in cost_str.lower():
                    cost_str = f"{cost_str} for two"

            # Explanation
            explanation = str(item.get("explanation") or "").strip()
            if not explanation:
                explanation = (
                    f"Selected as an excellent {cuisine} dining choice with a {rating:.1f} rating."
                )

            recommendations.append(
                Recommendation(
                    restaurant_name=clean_name,
                    cuisine=cuisine,
                    rating=round(rating, 1),
                    estimated_cost=cost_str,
                    explanation=explanation,
                )
            )
            seen_names.add(name_lower)

        return recommendations

    def generate_fallback(
        self,
        df: pd.DataFrame,
        preferences: UserPreferences | None = None,
        top_n: int = 5,
    ) -> list[Recommendation]:
        """
        Generate non-LLM recommendations directly from candidate DataFrame (Task 4.8).

        Returns top-N restaurants sorted by rating and votes with personalized
        rule-based explanations.
        """
        if df is None or df.empty:
            logger.warning("Empty DataFrame passed to generate_fallback.")
            return []

        # Sort by rating (desc) and votes (desc)
        sort_cols = [c for c in ["rating", "votes"] if c in df.columns]
        sorted_df = df.sort_values(by=sort_cols, ascending=[False] * len(sort_cols)) if sort_cols else df
        top_slice = sorted_df.head(top_n)

        prefs = preferences or UserPreferences()
        recommendations: list[Recommendation] = []

        for _, row in top_slice.iterrows():
            name = str(row.get("name", "Restaurant"))
            cuisine = str(row.get("cuisines", "Multi-Cuisine"))
            rating = float(row.get("rating", 4.0))
            cost = row.get("cost_for_two")
            cost_str = f"₹{int(cost)} for two" if pd.notna(cost) and cost else "₹800 for two"
            loc = str(row.get("location", "Bangalore"))
            votes = int(row.get("votes", 0))

            # Personalized fallback explanation
            reasons = [f"highly rated ({rating:.1f}⭐)"]
            if votes > 500:
                reasons.append(f"popular choice with {votes:,} reviews")
            if prefs.cuisine and prefs.cuisine.lower() in cuisine.lower():
                reasons.append(f"serves your requested {prefs.cuisine} cuisine")
            if prefs.budget and row.get("budget_category") == prefs.budget:
                reasons.append(f"matches your {prefs.budget} budget preference")

            explanation = (
                f"{name} in {loc} is a top dining spot that is {', '.join(reasons)}. "
                "Recommended based on verified diners and ratings."
            )

            recommendations.append(
                Recommendation(
                    restaurant_name=name,
                    cuisine=cuisine,
                    rating=round(rating, 1),
                    estimated_cost=cost_str,
                    explanation=explanation,
                )
            )

        return recommendations
