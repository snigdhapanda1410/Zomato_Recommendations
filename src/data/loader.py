"""
Dataset loader for the Zomato restaurant recommendation system.

Handles fetching the Zomato dataset from Hugging Face or loading from a local
parquet cache, including schema validation and error fallback.
"""

from typing import Iterable
import pandas as pd
from datasets import load_dataset

from src.data.cache import DatasetCache
from src.utils.config import AppConfig
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DatasetLoadError(Exception):
    """Raised when the dataset cannot be loaded from remote or local cache."""
    pass


class DatasetEmptyError(DatasetLoadError):
    """Raised when the loaded dataset has 0 rows."""
    pass


class DatasetLoader:
    """
    Loads the Zomato dataset from Hugging Face or local cache.

    Features:
    - Transparent caching via `DatasetCache`.
    - Schema validation for expected columns.
    - Fallback to cache during network interruptions.
    - Force-download override option.
    """

    # Essential columns required for recommendation and filtering
    REQUIRED_COLUMNS: tuple[str, ...] = (
        "name",
        "rate",
        "location",
        "cuisines",
        "approx_cost(for two people)",
    )

    def __init__(
        self,
        config: AppConfig | None = None,
        cache: DatasetCache | None = None,
    ) -> None:
        """
        Initialize the DatasetLoader.

        Args:
            config: Application configuration. Defaults to a new AppConfig instance.
            cache: DatasetCache instance. If None, created using config.cache_dir.
        """
        self.config = config or AppConfig()
        self.cache = cache or DatasetCache(self.config.cache_dir)
        self.cache_filename = "zomato_raw.parquet"

    def load(self, force_download: bool = False) -> pd.DataFrame:
        """
        Load the Zomato dataset.

        If caching is enabled and not force_download, attempts to load from local cache first.
        Otherwise, fetches from Hugging Face, validates the schema, and saves to cache.

        Args:
            force_download: If True, bypasses local cache and attempts a fresh download.

        Returns:
            pd.DataFrame: The loaded raw dataset.

        Raises:
            DatasetLoadError: If both download and cache loading fail, or schema is invalid.
        """
        # 1. Attempt cache load if enabled and not forced
        if self.config.cache_enabled and not force_download:
            cached_df = self.cache.load(self.cache_filename)
            if cached_df is not None and not cached_df.empty:
                logger.info(f"Using cached dataset with {len(cached_df):,} rows.")
                self._validate_schema(cached_df)
                return cached_df

        # 2. Fetch from Hugging Face
        logger.info(
            f"Fetching dataset '{self.config.dataset_name}' from Hugging Face..."
        )
        try:
            df = self._fetch_from_huggingface()
        except Exception as exc:
            logger.warning(
                f"Failed to fetch dataset from Hugging Face: {exc}. "
                "Attempting fallback to local cache..."
            )
            # Offline / network failure fallback
            cached_df = self.cache.load(self.cache_filename)
            if cached_df is not None and not cached_df.empty:
                logger.warning("Network download failed; using cached dataset fallback.")
                self._validate_schema(cached_df)
                return cached_df
            raise DatasetLoadError(
                f"Failed to download dataset '{self.config.dataset_name}' and no valid "
                f"cache found at '{self.cache.get_path(self.cache_filename)}': {exc}"
            ) from exc

        # 3. Validate loaded dataset
        self._validate_schema(df)

        # 4. Save to cache if enabled
        if self.config.cache_enabled:
            self.cache.save(df, self.cache_filename)

        return df

    def _fetch_from_huggingface(self) -> pd.DataFrame:
        """
        Fetch the dataset directly from Hugging Face Hub using the `datasets` library.

        Returns:
            pd.DataFrame: Raw dataset converted to Pandas.
        """
        ds = load_dataset(self.config.dataset_name, split="train")
        df = ds.to_pandas()
        return df

    def _validate_schema(
        self,
        df: pd.DataFrame,
        required_columns: Iterable[str] | None = None,
    ) -> None:
        """
        Validate that the DataFrame is non-empty and contains essential columns.

        Args:
            df: DataFrame to validate.
            required_columns: Iterable of required column names. Defaults to REQUIRED_COLUMNS.

        Raises:
            DatasetEmptyError: If DataFrame has 0 rows.
            DatasetLoadError: If any required column is missing.
        """
        if df is None or df.empty:
            raise DatasetEmptyError("Dataset is empty (0 rows).")

        cols_to_check = required_columns or self.REQUIRED_COLUMNS
        missing_cols = [col for col in cols_to_check if col not in df.columns]

        if missing_cols:
            raise DatasetLoadError(
                f"Dataset schema mismatch: missing required columns {missing_cols}. "
                f"Available columns: {list(df.columns)}"
            )
