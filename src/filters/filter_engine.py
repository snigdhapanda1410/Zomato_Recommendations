"""
Multi-criteria filtering engine with progressive constraint relaxation.

Filters preprocessed restaurant DataFrames based on user preferences (location,
budget, cuisine, rating) and gracefully relaxes constraints if results are too few.
"""

from dataclasses import dataclass, field
import pandas as pd

from src.utils.config import AppConfig
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class UserPreferences:
    """
    User preference inputs for filtering and recommendation.

    Fields:
        location: Target neighborhood or city (e.g., 'Koramangala', 'Bangalore').
        budget: Budget tier ('Low', 'Medium', 'High').
        cuisine: Desired cuisine type (e.g., 'Italian', 'North Indian').
        min_rating: Minimum restaurant rating threshold (0.0 to 5.0).
        additional_prefs: Free-text context for LLM (e.g., 'romantic, outdoor seating').
    """

    location: str | None = None
    budget: str | None = None
    cuisine: str | None = None
    min_rating: float = 0.0
    additional_prefs: str | None = None

    def __post_init__(self) -> None:
        """Sanitize and validate preferences."""
        if self.location is not None:
            self.location = str(self.location).strip()
            if not self.location:
                self.location = None

        if self.budget is not None:
            self.budget = str(self.budget).strip()
            if not self.budget:
                self.budget = None

        if self.cuisine is not None:
            self.cuisine = str(self.cuisine).strip()
            if not self.cuisine:
                self.cuisine = None

        if self.min_rating is not None:
            try:
                self.min_rating = float(self.min_rating)
                if self.min_rating < 0.0:
                    self.min_rating = 0.0
                elif self.min_rating > 5.0:
                    self.min_rating = 5.0
            except (ValueError, TypeError):
                self.min_rating = 0.0
        else:
            self.min_rating = 0.0

        if self.additional_prefs is not None:
            self.additional_prefs = str(self.additional_prefs).strip()
            # Truncate very long additional_prefs (UI-06, E10)
            if len(self.additional_prefs) > 500:
                logger.warning(
                    f"additional_prefs ({len(self.additional_prefs)} chars) exceeded "
                    "500 characters. Truncating."
                )
                self.additional_prefs = self.additional_prefs[:500]
            if not self.additional_prefs:
                self.additional_prefs = None

    def is_empty(self) -> bool:
        """Check if all preference criteria are unconstrained."""
        return (
            self.location is None
            and self.budget is None
            and self.cuisine is None
            and self.min_rating <= 0.0
            and self.additional_prefs is None
        )


@dataclass
class FilterResult:
    """
    Encapsulates the output of the filtering engine.

    Attributes:
        filtered_df: Resulting DataFrame of matching restaurants.
        relaxed_filters: List of filter names that were relaxed to meet min_results.
        total_matched: Total count of restaurants matching before truncation.
        is_truncated: True if results were capped at max_restaurants.
    """

    filtered_df: pd.DataFrame
    relaxed_filters: list[str] = field(default_factory=list)
    total_matched: int = 0
    is_truncated: bool = False

    @property
    def is_relaxed(self) -> bool:
        """True if any filters were loosened during processing."""
        return len(self.relaxed_filters) > 0

    def __len__(self) -> int:
        """Return the number of restaurants in filtered_df."""
        return len(self.filtered_df)


class FilterEngine:
    """
    Applies multi-criteria sequential AND filters with progressive relaxation.

    Relaxation strategy when results < min_results (default 3):
    1. Apply all filters strictly.
    2. Drop additional_prefs (recorded as relaxed).
    3. Drop min_rating constraint (set to 0.0).
    4. Drop budget tier constraint.
    5. Drop cuisine constraint.
    6. Drop location constraint (returns top-rated globally).
    """

    # City-wide aliases that match all records in Bangalore dataset
    CITY_WIDE_ALIASES = {"bangalore", "bengaluru", "all", "any"}

    def __init__(
        self,
        config: AppConfig | None = None,
        min_results: int = 3,
        max_results: int | None = None,
    ) -> None:
        """
        Initialize FilterEngine.

        Args:
            config: AppConfig containing max_restaurants_to_llm setting.
            min_results: Minimum matching restaurants required before triggering relaxation.
            max_results: Maximum restaurants to return to prevent prompt overflow.
                         If None, defaults to config.max_restaurants_to_llm.
        """
        self.config = config or AppConfig()
        self.min_results = min_results
        self.max_results = (
            max_results
            if max_results is not None
            else self.config.max_restaurants_to_llm
        )

    def filter(
        self,
        df: pd.DataFrame,
        prefs: UserPreferences | None = None,
    ) -> FilterResult:
        """
        Apply user preferences to filter the dataset.

        Args:
            df: Cleaned restaurant DataFrame from preprocessor.
            prefs: UserPreferences instance. Defaults to empty preferences.

        Returns:
            FilterResult: Filtered DataFrame, relaxed filters list, and metadata.
        """
        if df is None or df.empty:
            logger.warning("Empty DataFrame passed to FilterEngine.")
            return FilterResult(filtered_df=pd.DataFrame(), total_matched=0)

        preferences = prefs or UserPreferences()

        # Step 1: Apply all filters strictly
        strict_df = self._apply_filters(
            df=df,
            location=preferences.location,
            budget=preferences.budget,
            cuisine=preferences.cuisine,
            min_rating=preferences.min_rating,
        )

        if len(strict_df) >= self.min_results:
            logger.info(f"Strict filter found {len(strict_df)} matching restaurants.")
            return self._build_result(strict_df, relaxed_filters=[])

        # If results < min_results, initiate progressive relaxation
        logger.info(
            f"Strict filter returned only {len(strict_df)} results "
            f"(< minimum {self.min_results}). Starting progressive relaxation..."
        )

        relaxed_df, relaxed_filters = self._relax_and_retry(
            df=df,
            prefs=preferences,
            strict_matches=strict_df,
        )

        return self._build_result(relaxed_df, relaxed_filters=relaxed_filters)

    def _apply_filters(
        self,
        df: pd.DataFrame,
        location: str | None,
        budget: str | None,
        cuisine: str | None,
        min_rating: float,
    ) -> pd.DataFrame:
        """Apply active sequential AND filters."""
        if df.empty:
            return df

        result = df

        if location:
            result = self._filter_by_location(result, location)
            if result.empty:
                return result

        if budget:
            result = self._filter_by_budget(result, budget)
            if result.empty:
                return result

        if cuisine:
            result = self._filter_by_cuisine(result, cuisine)
            if result.empty:
                return result

        if min_rating and min_rating > 0.0:
            result = self._filter_by_rating(result, min_rating)

        return result

    def _filter_by_location(self, df: pd.DataFrame, location: str | None) -> pd.DataFrame:
        """
        Filter restaurants by location (case-insensitive substring match).

        Recognizes city-wide aliases ('Bangalore', 'Bengaluru', 'All') as matching all.
        """
        if df.empty or not location or "location" not in df.columns:
            return df

        loc_clean = location.strip().lower()
        if loc_clean in self.CITY_WIDE_ALIASES:
            return df

        if df["location"].isna().all():
            logger.warning("Location column is entirely null. Skipping location filter.")
            return df

        mask = df["location"].astype(str).str.lower().str.contains(loc_clean, regex=False, na=False)
        return df[mask]

    def _filter_by_budget(self, df: pd.DataFrame, budget: str | None) -> pd.DataFrame:
        """
        Filter restaurants by budget tier ('Low', 'Medium', 'High').
        """
        if df.empty or not budget or "budget_category" not in df.columns:
            return df

        b_clean = budget.strip().lower()
        if b_clean in ("all", "any"):
            return df

        if df["budget_category"].isna().all():
            logger.warning("budget_category column is entirely null. Skipping budget filter.")
            return df

        mask = df["budget_category"].astype(str).str.lower() == b_clean
        return df[mask]

    def _filter_by_cuisine(self, df: pd.DataFrame, cuisine: str | None) -> pd.DataFrame:
        """
        Filter restaurants by cuisine (case-insensitive partial match).
        """
        if df.empty or not cuisine or "cuisines" not in df.columns:
            return df

        c_clean = cuisine.strip().lower()
        if c_clean in ("all", "any"):
            return df

        if df["cuisines"].isna().all():
            logger.warning("cuisines column is entirely null. Skipping cuisine filter.")
            return df

        mask = df["cuisines"].astype(str).str.lower().str.contains(c_clean, regex=False, na=False)
        return df[mask]

    def _filter_by_rating(self, df: pd.DataFrame, min_rating: float) -> pd.DataFrame:
        """
        Filter restaurants with rating >= min_rating.
        """
        if df.empty or min_rating <= 0.0 or "rating" not in df.columns:
            return df

        if df["rating"].isna().all():
            logger.warning("rating column is entirely null. Skipping rating filter.")
            return df

        mask = df["rating"] >= min_rating
        return df[mask]

    def _relax_and_retry(
        self,
        df: pd.DataFrame,
        prefs: UserPreferences,
        strict_matches: pd.DataFrame,
    ) -> tuple[pd.DataFrame, list[str]]:
        """
        Execute progressive relaxation steps until >= min_results or all relaxed.

        Relaxation Order:
        1. Drop additional_prefs
        2. Drop min_rating (set to 0.0)
        3. Drop budget tier
        4. Drop cuisine
        5. Drop location (global top-rated)
        """
        relaxed_filters: list[str] = []
        curr_loc = prefs.location
        curr_budget = prefs.budget
        curr_cuisine = prefs.cuisine
        curr_rating = prefs.min_rating

        # Step 2: Drop additional_prefs (if user provided any)
        if prefs.additional_prefs:
            relaxed_filters.append("additional_prefs")

        # Step 3: Drop min_rating
        if curr_rating > 0.0:
            relaxed_filters.append("min_rating")
            curr_rating = 0.0
            attempt_df = self._apply_filters(
                df, location=curr_loc, budget=curr_budget, cuisine=curr_cuisine, min_rating=curr_rating
            )
            merged = self._merge_with_strict(strict_matches, attempt_df)
            if len(merged) >= self.min_results:
                logger.info(f"Relaxed min_rating -> found {len(merged)} results.")
                return merged, relaxed_filters

        # Step 4: Drop budget
        if curr_budget:
            relaxed_filters.append("budget")
            curr_budget = None
            attempt_df = self._apply_filters(
                df, location=curr_loc, budget=curr_budget, cuisine=curr_cuisine, min_rating=curr_rating
            )
            merged = self._merge_with_strict(strict_matches, attempt_df)
            if len(merged) >= self.min_results:
                logger.info(f"Relaxed budget -> found {len(merged)} results.")
                return merged, relaxed_filters

        # Step 5: Drop cuisine
        if curr_cuisine:
            relaxed_filters.append("cuisine")
            curr_cuisine = None
            attempt_df = self._apply_filters(
                df, location=curr_loc, budget=curr_budget, cuisine=curr_cuisine, min_rating=curr_rating
            )
            merged = self._merge_with_strict(strict_matches, attempt_df)
            if len(merged) >= self.min_results:
                logger.info(f"Relaxed cuisine -> found {len(merged)} results.")
                return merged, relaxed_filters

        # Step 6: Drop location (last resort fallback to global dataset)
        if curr_loc:
            relaxed_filters.append("location")
            curr_loc = None
            attempt_df = self._apply_filters(
                df, location=curr_loc, budget=curr_budget, cuisine=curr_cuisine, min_rating=curr_rating
            )
            merged = self._merge_with_strict(strict_matches, attempt_df)
            if len(merged) >= self.min_results:
                logger.info(f"Relaxed location -> found {len(merged)} results.")
                return merged, relaxed_filters

        # If still < min_results, return merged or all available sorted
        final_df = self._merge_with_strict(strict_matches, df)
        return final_df, relaxed_filters

    def _merge_with_strict(
        self,
        strict_df: pd.DataFrame,
        relaxed_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Merge strict matches with relaxed matches, ensuring strict matches appear first
        and avoiding duplicate entries (FE-02).
        """
        if strict_df.empty:
            return relaxed_df.copy()

        if relaxed_df.empty:
            return strict_df.copy()

        # Combine with strict matches on top, then drop duplicates by (name, location)
        combined = pd.concat([strict_df, relaxed_df], ignore_index=True)
        dedup_cols = [c for c in ["name", "location"] if c in combined.columns]
        if dedup_cols:
            combined = combined.drop_duplicates(subset=dedup_cols, keep="first")
        return combined

    def _build_result(
        self,
        df: pd.DataFrame,
        relaxed_filters: list[str],
    ) -> FilterResult:
        """
        Sort and truncate results to max_results (Task 3.5), packaging into FilterResult.
        """
        total_matched = len(df)

        if df.empty:
            return FilterResult(
                filtered_df=df,
                relaxed_filters=relaxed_filters,
                total_matched=0,
                is_truncated=False,
            )

        # Sort by rating (descending), then votes (descending)
        sort_cols = [c for c in ["rating", "votes"] if c in df.columns]
        if sort_cols:
            df = df.sort_values(by=sort_cols, ascending=[False] * len(sort_cols))

        is_truncated = len(df) > self.max_results
        if is_truncated:
            logger.info(
                f"Truncating {len(df)} results to top {self.max_results} "
                "for LLM context window."
            )
            df = df.iloc[: self.max_results].copy()

        df = df.reset_index(drop=True)

        return FilterResult(
            filtered_df=df,
            relaxed_filters=relaxed_filters,
            total_matched=total_matched,
            is_truncated=is_truncated,
        )
