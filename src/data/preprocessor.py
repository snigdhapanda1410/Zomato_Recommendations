"""
Data preprocessing pipeline for the Zomato dataset.

Cleans, normalizes, and categorizes restaurant data for downstream filtering
and LLM prompt building.
"""

import re
import pandas as pd

from src.utils.config import AppConfig
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataPreprocessor:
    """
    Transforms raw Zomato dataset into a cleaned, standardized DataFrame.

    Preprocessing steps:
    1. Standardize column names (mapping raw Hugging Face fields).
    2. Drop records missing crucial identifiers ('name' or 'rating').
    3. Normalize ratings to a clean 0.0 - 5.0 float scale.
    4. Clean cost values and categorize into Low, Medium, and High budget buckets.
    5. Clean and title-case cuisine tokens.
    6. Standardize location names.
    7. Clean flags (online_order, book_table) and vote counts.
    8. Deduplicate on (name, location), prioritizing highest-rated entries.
    9. Select and order standardized output columns.
    """

    FINAL_COLUMNS = [
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

    def __init__(self, config: AppConfig | None = None) -> None:
        """
        Initialize DataPreprocessor.

        Args:
            config: AppConfig instance containing budget thresholds.
        """
        self.config = config or AppConfig()

    def preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Execute full preprocessing pipeline on the input DataFrame.

        Args:
            df: Raw DataFrame (e.g. from Hugging Face or raw cache).

        Returns:
            pd.DataFrame: Cleaned and standardized DataFrame.
        """
        if df is None or df.empty:
            logger.warning("Empty DataFrame passed to preprocessor.")
            return pd.DataFrame(columns=self.FINAL_COLUMNS)

        logger.info(f"Starting data preprocessing on {len(df):,} raw rows...")
        processed = df.copy()

        processed = self._standardize_column_names(processed)
        processed = self._sanitize_names(processed)
        processed = self._normalize_ratings(processed)
        processed = self._clean_costs(processed)
        processed = self._categorize_budget(processed)
        processed = self._clean_cuisines(processed)
        processed = self._standardize_location(processed)
        processed = self._clean_flags_and_votes(processed)
        processed = self._deduplicate(processed)
        processed = self._select_columns(processed)

        logger.info(
            f"Preprocessing completed. Output contains {len(processed):,} clean rows."
        )
        return processed

    def _standardize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rename raw columns to canonical column names."""
        mapping = {
            "name": "name",
            "restaurant_name": "name",
            "rate": "rating",
            "rating": "rating",
            "approx_cost(for two people)": "cost_for_two",
            "cost_for_two": "cost_for_two",
            "cost": "cost_for_two",
            "location": "location",
            "cuisines": "cuisines",
            "cuisine": "cuisines",
            "votes": "votes",
            "online_order": "online_order",
            "book_table": "book_table",
        }

        rename_dict = {}
        for col in df.columns:
            if col in mapping and mapping[col] != col:
                rename_dict[col] = mapping[col]

        return df.rename(columns=rename_dict)

    def _sanitize_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Strip HTML tags, extra whitespace, and drop rows with empty names.
        """
        if "name" not in df.columns:
            return df

        # Drop null or empty names
        df = df[df["name"].notna()].copy()

        def clean_name(val: str) -> str:
            if not isinstance(val, str):
                val = str(val)
            # Remove HTML tags if present (PP-10)
            cleaned = re.sub(r"<[^>]+>", "", val)
            return cleaned.strip()

        df["name"] = df["name"].apply(clean_name)
        df = df[df["name"].str.len() > 0]
        return df

    def _normalize_ratings(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize ratings to a 0.0 - 5.0 float scale.
        Drops rows where rating is invalid, missing, or non-numeric ('NEW', '-').
        Clips ratings to [0.0, 5.0].
        """
        if "rating" not in df.columns:
            return df

        def parse_rating(val) -> float | None:
            if pd.isna(val):
                return None
            val_str = str(val).strip()
            if val_str in ("NEW", "-", "nan", ""):
                return None
            # Handle formats like "4.1/5", "3.8 /5", "4.2"
            if "/5" in val_str:
                val_str = val_str.split("/5")[0].strip()
            try:
                num = float(val_str)
                # Clip to 0.0 - 5.0 (PP-02)
                if num < 0.0:
                    logger.debug(f"Negative rating {num} clipped to 0.0")
                    num = 0.0
                elif num > 5.0:
                    logger.debug(f"Out of range rating {num} clipped to 5.0")
                    num = 5.0
                return round(num, 1)
            except ValueError:
                return None

        df["rating"] = df["rating"].apply(parse_rating)
        # Drop rows missing rating as required by implementation plan and PP-01
        df = df[df["rating"].notna()].copy()
        df["rating"] = df["rating"].astype(float)
        return df

    def _clean_costs(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean cost string (removing commas, currency signs) and extract numeric value.
        """
        if "cost_for_two" not in df.columns:
            df["cost_for_two"] = 0
            return df

        def parse_cost(val) -> int | None:
            if pd.isna(val):
                return None
            val_str = str(val).strip().replace(",", "")
            # Extract digits
            match = re.search(r"(\d+)", val_str)
            if not match:
                return None
            cost = int(match.group(1))
            if cost <= 0:
                return None
            if cost > 10000:
                logger.warning(f"Extremely high cost detected (₹{cost:,}). Categorizing as High.")
            return cost

        df["cost_for_two"] = df["cost_for_two"].apply(parse_cost)
        return df

    def _categorize_budget(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Map cost_for_two into budget buckets:
        - <= budget_low_max: 'Low'
        - budget_low_max < cost <= budget_medium_max: 'Medium'
        - > budget_medium_max: 'High'
        - None / <= 0: 'Unknown'
        """
        low_max = self.config.budget_low_max
        med_max = self.config.budget_medium_max

        def get_category(cost) -> str:
            if pd.isna(cost) or cost is None or cost <= 0:
                return "Unknown"
            if cost <= low_max:
                return "Low"
            if cost <= med_max:
                return "Medium"
            return "High"

        df["budget_category"] = df["cost_for_two"].apply(get_category)
        return df

    def _clean_cuisines(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize cuisine labels by trimming whitespace and title-casing each cuisine.
        """
        if "cuisines" not in df.columns:
            df["cuisines"] = "Unknown"
            return df

        def format_cuisine(val) -> str:
            if pd.isna(val) or not str(val).strip():
                return "Unknown"
            parts = [p.strip().title() for p in str(val).split(",") if p.strip()]
            return ", ".join(parts) if parts else "Unknown"

        df["cuisines"] = df["cuisines"].apply(format_cuisine)
        return df

    def _standardize_location(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize location names with whitespace trimming and title-casing."""
        if "location" not in df.columns:
            df["location"] = "Unknown"
            return df

        def format_location(val) -> str:
            if pd.isna(val) or not str(val).strip():
                return "Unknown"
            return str(val).strip().title()

        df["location"] = df["location"].apply(format_location)
        return df

    def _clean_flags_and_votes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize votes (integer >= 0) and boolean flags (online_order, book_table).
        """
        # Votes
        if "votes" in df.columns:
            df["votes"] = pd.to_numeric(df["votes"], errors="coerce").fillna(0).astype(int)
            df["votes"] = df["votes"].clip(lower=0)
        else:
            df["votes"] = 0

        # Helper for Yes/No flags
        def clean_yes_no(val) -> str:
            if pd.isna(val):
                return "No"
            val_str = str(val).strip().lower()
            if val_str in ("yes", "true", "1", "y"):
                return "Yes"
            return "No"

        for flag_col in ("online_order", "book_table"):
            if flag_col in df.columns:
                df[flag_col] = df[flag_col].apply(clean_yes_no)
            else:
                df[flag_col] = "No"

        return df

    def _deduplicate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Deduplicate restaurants by (name, location).
        Keeps the entry with the highest rating and votes.
        """
        # Sort so highest rating and highest votes appear first
        sort_cols = [col for col in ["rating", "votes"] if col in df.columns]
        if sort_cols:
            df = df.sort_values(by=sort_cols, ascending=[False] * len(sort_cols))

        dedup_subset = [col for col in ["name", "location"] if col in df.columns]
        if dedup_subset:
            before_count = len(df)
            df = df.drop_duplicates(subset=dedup_subset, keep="first")
            dropped = before_count - len(df)
            if dropped > 0:
                logger.info(f"Deduplicated {dropped:,} duplicate restaurant entries.")

        return df

    def _select_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure all required columns exist and order them cleanly."""
        for col in self.FINAL_COLUMNS:
            if col not in df.columns:
                df[col] = "Unknown" if col in ("cuisines", "location", "budget_category") else 0

        df = df[self.FINAL_COLUMNS].copy()
        df = df.reset_index(drop=True)
        return df

    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convenience wrapper matching architectural interface for filling/dropping
        missing values.
        """
        df = self._sanitize_names(df)
        df = self._normalize_ratings(df)
        return df
