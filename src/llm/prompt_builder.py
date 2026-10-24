"""
Prompt engineering and construction for restaurant recommendations.

Constructs structured prompts combining user preferences and candidate restaurant
data to elicit grounded JSON recommendations from the LLM.
"""

import pandas as pd

from src.filters.filter_engine import UserPreferences
from src.utils.config import AppConfig
from src.utils.logger import get_logger

logger = get_logger(__name__)


PROMPT_TEMPLATE = """You are an expert food critic and restaurant recommendation assistant.
Your goal is to help users find the perfect restaurant based on their preferences.

## USER PREFERENCES
- Location: {location}
- Budget: {budget}
- Preferred Cuisine: {cuisine}
- Minimum Rating: {min_rating}
- Additional Preferences: {additional_prefs}

## AVAILABLE RESTAURANTS
{restaurant_table}

## YOUR TASK
From the restaurants listed above, select the top {top_n} that BEST match
the user's preferences. For each restaurant, provide:

1. restaurant_name — exact name from the list
2. cuisine — cuisine types offered
3. rating — the restaurant's rating
4. estimated_cost — approximate cost for two (e.g., '₹800 for two')
5. explanation — 2-3 sentences explaining WHY this restaurant is a great
   match for the user's specific preferences

IMPORTANT:
- ONLY recommend restaurants from the provided list
- Rank from best match to least
- Consider ALL user preferences when ranking

## OUTPUT FORMAT
Respond ONLY with a valid JSON array:
[
  {{
    "restaurant_name": "...",
    "cuisine": "...",
    "rating": 4.5,
    "estimated_cost": "₹800 for two",
    "explanation": "..."
  }}
]"""


class PromptBuilder:
    """
    Builds structured prompts for LLM restaurant recommendations.

    Features:
    - Injects sanitized user preferences.
    - Formats tabular restaurant data into Markdown tables.
    - Specifies strict JSON schema and groundedness constraints.
    """

    def __init__(self, config: AppConfig | None = None) -> None:
        """
        Initialize PromptBuilder.

        Args:
            config: Optional application configuration.
        """
        self.config = config or AppConfig()

    def build_recommendation_prompt(
        self,
        restaurants: pd.DataFrame,
        preferences: UserPreferences | None = None,
        top_n: int = 5,
    ) -> str:
        """
        Construct the recommendation prompt.

        Args:
            restaurants: DataFrame of filtered candidate restaurants.
            preferences: User preferences instance.
            top_n: Number of recommendations requested.

        Returns:
            str: Fully formatted prompt ready for LLM inference.
        """
        prefs = preferences or UserPreferences()

        # Sanitize preference strings (prevent prompt escaping/formatting issues)
        loc = (prefs.location or "Any (Bangalore)").replace("{", "(").replace("}", ")")
        budget = (prefs.budget or "Any").replace("{", "(").replace("}", ")")
        cuisine = (prefs.cuisine or "Any").replace("{", "(").replace("}", ")")
        min_rat = f"{prefs.min_rating}/5" if prefs.min_rating > 0.0 else "None"
        add_prefs = (
            prefs.additional_prefs.replace("{", "(").replace("}", ")")
            if prefs.additional_prefs
            else "None"
        )

        table_str = self._format_restaurant_table(restaurants)

        prompt = PROMPT_TEMPLATE.format(
            location=loc,
            budget=budget,
            cuisine=cuisine,
            min_rating=min_rat,
            additional_prefs=add_prefs,
            restaurant_table=table_str,
            top_n=top_n,
        )

        logger.debug(f"Built prompt for {len(restaurants)} candidate restaurants.")
        return prompt

    def _format_restaurant_table(self, df: pd.DataFrame) -> str:
        """
        Format DataFrame into a compact Markdown table for prompt injection.
        """
        if df is None or df.empty:
            return "No restaurants currently available."

        headers = [
            "Name",
            "Location",
            "Cuisines",
            "Budget",
            "Cost for Two",
            "Rating",
            "Votes",
        ]
        lines = [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |",
        ]

        for _, row in df.iterrows():
            name = str(row.get("name", "Unknown")).replace("|", "-")
            loc = str(row.get("location", "Unknown")).replace("|", "-")
            cuisines = str(row.get("cuisines", "Unknown")).replace("|", "-")
            budget = str(row.get("budget_category", "Unknown"))
            cost_val = row.get("cost_for_two")
            cost_str = f"₹{int(cost_val)}" if pd.notna(cost_val) and cost_val else "Unknown"
            rating = f"{float(row.get('rating', 0.0)):.1f}"
            votes = str(int(row.get("votes", 0)))

            lines.append(
                f"| {name} | {loc} | {cuisines} | {budget} | {cost_str} | {rating} | {votes} |"
            )

        return "\n".join(lines)
