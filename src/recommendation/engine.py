"""
Central orchestrator engine for the Zomato AI Restaurant Recommendation System.

Coordinates data loading, preprocessing, multi-criteria filtering, prompt building,
LLM inference via Groq, and response parsing with robust fallbacks.
"""

from dataclasses import dataclass, field
from pathlib import Path
import time
from typing import Any, Iterator
import pandas as pd

from src.data.loader import DatasetLoader
from src.data.preprocessor import DataPreprocessor
from src.filters.filter_engine import FilterEngine, FilterResult, UserPreferences
from src.llm.llm_client import LLMClient, LLMError
from src.llm.prompt_builder import PromptBuilder
from src.llm.response_parser import Recommendation, ResponseParser
from src.utils.config import AppConfig
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RecommendationResult:
    """
    Result container encapsulating recommendations and execution metadata.

    Attributes:
        recommendations: List of parsed Recommendation objects.
        total_matches: Number of matching restaurants found before LLM ranking.
        filters_applied: Dictionary of active user preferences.
        filters_relaxed: List of filter constraints relaxed to satisfy min_results.
        is_fallback: True if recommendations were generated via rule-based fallback.
        fallback_reason: Description of why fallback was triggered (if applicable).
    """

    recommendations: list[Recommendation] = field(default_factory=list)
    total_matches: int = 0
    filters_applied: dict[str, Any] = field(default_factory=dict)
    filters_relaxed: list[str] = field(default_factory=list)
    is_fallback: bool = False
    fallback_reason: str | None = None

    def __iter__(self) -> Iterator[Recommendation]:
        """Allow direct iteration over recommendations."""
        return iter(self.recommendations)

    def __len__(self) -> int:
        """Return number of recommendations."""
        return len(self.recommendations)

    def __getitem__(self, index: int) -> Recommendation:
        """Allow indexed access to recommendations."""
        return self.recommendations[index]


class RecommendationEngine:
    """
    Coordinates the full end-to-end restaurant recommendation pipeline.

    Flow:
    1. Load and preprocess dataset (transparent caching via DatasetCache).
    2. Filter candidate restaurants based on UserPreferences with relaxation.
    3. Truncate candidates to top-N (max 50) for LLM context window safety.
    4. Construct grounded prompt with candidate table and user preferences.
    5. Call Groq LLM API with retries and exponential backoff.
    6. Parse JSON response into Recommendation objects, validating names against candidates.
    7. Gracefully fallback to deterministic ranking if LLM API is unavailable or errors.
    """

    def __init__(
        self,
        loader: DatasetLoader | None = None,
        preprocessor: DataPreprocessor | None = None,
        filter_engine: FilterEngine | None = None,
        prompt_builder: PromptBuilder | None = None,
        llm_client: LLMClient | None = None,
        response_parser: ResponseParser | None = None,
        config: AppConfig | None = None,
        preprocessed_df: pd.DataFrame | None = None,
    ) -> None:
        """
        Initialize RecommendationEngine with dependencies.

        Args:
            loader: DatasetLoader instance.
            preprocessor: DataPreprocessor instance.
            filter_engine: FilterEngine instance.
            prompt_builder: PromptBuilder instance.
            llm_client: LLMClient instance.
            response_parser: ResponseParser instance.
            config: AppConfig configuration instance.
            preprocessed_df: Optional pre-loaded clean DataFrame to avoid redundant loading.
        """
        self.config = config or AppConfig()
        self.loader = loader or DatasetLoader(self.config)
        self.preprocessor = preprocessor or DataPreprocessor(self.config)
        self.filter_engine = filter_engine or FilterEngine(self.config)
        self.prompt_builder = prompt_builder or PromptBuilder(self.config)
        self.response_parser = response_parser or ResponseParser()
        self.llm_client = llm_client or LLMClient(config=self.config)

        self._preprocessed_df: pd.DataFrame | None = preprocessed_df

    @classmethod
    def from_config(cls, config: AppConfig | None = None) -> "RecommendationEngine":
        """
        Factory method to construct RecommendationEngine directly from AppConfig.

        Args:
            config: Optional AppConfig instance. If None, loaded from environment.

        Returns:
            RecommendationEngine: Fully initialized engine instance.
        """
        cfg = config or AppConfig()
        return cls(
            loader=DatasetLoader(cfg),
            preprocessor=DataPreprocessor(cfg),
            filter_engine=FilterEngine(cfg),
            prompt_builder=PromptBuilder(cfg),
            llm_client=LLMClient(config=cfg),
            response_parser=ResponseParser(),
            config=cfg,
        )

    def get_preprocessed_data(self, force_reload: bool = False) -> pd.DataFrame:
        """
        Retrieve preprocessed dataset, caching in memory on the engine instance.

        Args:
            force_reload: If True, reloads and re-preprocesses from raw source/cache.

        Returns:
            pd.DataFrame: Cleaned and standardized restaurant dataset.
        """
        if self._preprocessed_df is None or force_reload:
            # Check for bundled clean production dataset first (fastest boot, zero network latency)
            candidate_paths = [
                Path(self.config.cache_dir).parent / "zomato_clean.parquet",
                Path(__file__).resolve().parent.parent.parent / "data" / "zomato_clean.parquet",
            ]
            for clean_path in candidate_paths:
                if clean_path.exists() and not force_reload:
                    try:
                        self._preprocessed_df = pd.read_parquet(clean_path)
                        logger.info(
                            f"Loaded bundled clean dataset from '{clean_path}' "
                            f"with {len(self._preprocessed_df):,} restaurants."
                        )
                        return self._preprocessed_df
                    except Exception as exc:
                        logger.warning(
                            f"Failed to load bundled clean dataset from '{clean_path}': {exc}."
                        )


            logger.info("Loading and preprocessing dataset for RecommendationEngine...")
            raw_df = self.loader.load(force_download=force_reload)
            self._preprocessed_df = self.preprocessor.preprocess(raw_df)
            logger.info(
                f"Dataset ready with {len(self._preprocessed_df):,} restaurants."
            )
        return self._preprocessed_df

    def get_available_locations(self) -> list[str]:
        """
        Get sorted list of unique locations present in the clean dataset.

        Returns:
            list[str]: Sorted unique location names.
        """
        df = self.get_preprocessed_data()
        if "location" not in df.columns:
            return []
        locations = (
            df["location"].dropna().loc[lambda x: x.str.strip() != ""].unique()
        )
        return sorted([str(loc) for loc in locations])

    def get_available_cuisines(self) -> list[str]:
        """
        Get sorted list of unique individual cuisine tags present in the clean dataset.

        Returns:
            list[str]: Sorted unique cuisine names.
        """
        df = self.get_preprocessed_data()
        if "cuisines" not in df.columns:
            return []
        cuisines_set: set[str] = set()
        for item in df["cuisines"].dropna():
            for c in str(item).split(","):
                clean_c = c.strip()
                if clean_c and clean_c.lower() != "unknown":
                    cuisines_set.add(clean_c)
        return sorted(cuisines_set)

    def recommend(
        self,
        preferences: UserPreferences,
        top_n: int | None = None,
    ) -> RecommendationResult:
        """
        Execute end-to-end recommendation pipeline for given preferences.

        Args:
            preferences: UserPreferences input (location, budget, cuisine, rating, prefs).
            top_n: Number of recommendations to return (defaults to config.top_n_recommendations).

        Returns:
            RecommendationResult: Encapsulating recommendations, matched count, and relaxation info.
        """
        target_top_n = top_n or self.config.top_n_recommendations
        df = self.get_preprocessed_data()

        # Build dict of active filters applied
        filters_applied: dict[str, Any] = {}
        if preferences.location:
            filters_applied["location"] = preferences.location
        if preferences.budget:
            filters_applied["budget"] = preferences.budget
        if preferences.cuisine:
            filters_applied["cuisine"] = preferences.cuisine
        if preferences.min_rating > 0:
            filters_applied["min_rating"] = preferences.min_rating
        if preferences.additional_prefs:
            filters_applied["additional_prefs"] = preferences.additional_prefs

        logger.info(f"Filtering dataset with preferences: {filters_applied}")
        filter_result: FilterResult = self.filter_engine.filter(df, preferences)
        filtered_df = filter_result.filtered_df
        total_matched = filter_result.total_matched
        relaxed_filters = list(filter_result.relaxed_filters)

        # Edge case: absolutely 0 matching rows even after relaxation (e.g. empty dataset)
        if filtered_df.empty:
            logger.warning(
                "Filter returned 0 restaurants. Falling back to global top-rated."
            )
            fallback_recs = self.response_parser.generate_fallback(
                df, preferences=preferences, top_n=target_top_n
            )
            return RecommendationResult(
                recommendations=fallback_recs,
                total_matches=0,
                filters_applied=filters_applied,
                filters_relaxed=relaxed_filters,
                is_fallback=True,
                fallback_reason="No matching restaurants found after filtering.",
            )

        # Build prompt for LLM
        prompt = self.prompt_builder.build_recommendation_prompt(
            filtered_df, preferences=preferences, top_n=target_top_n
        )

        start_time = time.time()
        logger.info(
            f"[REQUEST START] User preferences: {filters_applied} | Requested top_n: {target_top_n}"
        )

        # Attempt LLM generation
        try:
            logger.info(
                f"Requesting recommendations from LLM ({self.config.llm_model})..."
            )
            raw_response = self.llm_client.generate(prompt)
            # Log LLM response preview for debugging (Task 6.8)
            resp_preview = (raw_response[:200] + "...") if len(raw_response) > 200 else raw_response
            logger.info(f"[LLM RESPONSE RECEIVED] Length: {len(raw_response)} chars | Preview: {resp_preview}")

            recommendations = self.response_parser.parse(
                raw_response, available_restaurants=filtered_df
            )

            elapsed_ms = (time.time() - start_time) * 1000
            # Check if LLM returned any valid recommendations
            if recommendations:
                rec_names = [r.restaurant_name for r in recommendations[:target_top_n]]
                logger.info(
                    f"[REQUEST COMPLETE] Generated {len(recommendations)} recommendations in {elapsed_ms:.1f}ms: {rec_names}"
                )
                return RecommendationResult(
                    recommendations=recommendations[:target_top_n],
                    total_matches=total_matched,
                    filters_applied=filters_applied,
                    filters_relaxed=relaxed_filters,
                    is_fallback=False,
                )
            else:
                logger.warning(
                    f"[REQUEST FALLBACK] LLM produced 0 valid parsed recommendations in {elapsed_ms:.1f}ms. Falling back to rule-based ranking."
                )
                fallback_recs = self.response_parser.generate_fallback(
                    filtered_df, preferences=preferences, top_n=target_top_n
                )
                return RecommendationResult(
                    recommendations=fallback_recs,
                    total_matches=total_matched,
                    filters_applied=filters_applied,
                    filters_relaxed=relaxed_filters,
                    is_fallback=True,
                    fallback_reason="LLM response did not contain parseable recommendations.",
                )

        except (LLMError, Exception) as exc:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.warning(
                f"[REQUEST FALLBACK] LLM generation failed ({exc}) after {elapsed_ms:.1f}ms. Falling back to rule-based ranking."
            )
            fallback_recs = self.response_parser.generate_fallback(
                filtered_df, preferences=preferences, top_n=target_top_n
            )
            return RecommendationResult(
                recommendations=fallback_recs,
                total_matches=total_matched,
                filters_applied=filters_applied,
                filters_relaxed=relaxed_filters,
                is_fallback=True,
                fallback_reason=str(exc),
            )
