"""
Cache management for dataset storage and retrieval.

Provides local caching of DataFrames in Apache Parquet format to enable fast
subsequent loads and offline resilience.
"""

from pathlib import Path
import shutil
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)


class DatasetCache:
    """
    Manages local filesystem caching of DataFrames as Parquet files.

    Features:
    - Thread-safe / process-safe file operations with error resilience.
    - Automatic creation of the cache directory.
    - Integrity validation on load (handles corrupt or zero-byte files).
    - Disk write failure handling (logs warning without crashing).
    """

    def __init__(self, cache_dir: Path | str = "./data/cache") -> None:
        """
        Initialize DatasetCache.

        Args:
            cache_dir: Directory where parquet cache files are stored.
        """
        self.cache_dir = Path(cache_dir)

    def _ensure_dir(self) -> None:
        """Create cache directory if it does not already exist."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.warning(f"Could not create cache directory '{self.cache_dir}': {e}")

    def get_path(self, filename: str = "zomato_raw.parquet") -> Path:
        """Get the absolute/resolved Path for a given cache filename."""
        return self.cache_dir / filename

    def exists(self, filename: str = "zomato_raw.parquet") -> bool:
        """
        Check if a cache file exists and has non-zero size.

        Args:
            filename: Name of the cache file.

        Returns:
            True if file exists and has size > 0, False otherwise.
        """
        cache_file = self.get_path(filename)
        return cache_file.exists() and cache_file.is_file() and cache_file.stat().st_size > 0

    def save(self, df: pd.DataFrame, filename: str = "zomato_raw.parquet") -> Path | None:
        """
        Save DataFrame to local cache in Parquet format.

        Args:
            df: DataFrame to save.
            filename: Target cache filename.

        Returns:
            Path to saved file if successful, None if saving failed.
        """
        if df is None or df.empty:
            logger.warning("Attempted to cache an empty or None DataFrame. Skipping.")
            return None

        self._ensure_dir()
        cache_file = self.get_path(filename)

        try:
            df.to_parquet(cache_file, index=False)
            logger.info(f"Successfully cached dataset ({len(df):,} rows) to '{cache_file}'")
            return cache_file
        except OSError as e:
            logger.warning(f"Failed to write cache file '{cache_file}' (disk space or permissions): {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error while saving cache to '{cache_file}': {e}")
            return None

    def load(self, filename: str = "zomato_raw.parquet") -> pd.DataFrame | None:
        """
        Load DataFrame from local cache.

        Validates that the file exists, is non-empty, and can be read as Parquet.
        If the file is corrupted, it is automatically removed and None is returned.

        Args:
            filename: Cache filename to load.

        Returns:
            Loaded pd.DataFrame if successful, None otherwise.
        """
        cache_file = self.get_path(filename)

        if not self.exists(filename):
            return None

        try:
            df = pd.read_parquet(cache_file)
            if df.empty:
                logger.warning(f"Cache file '{cache_file}' is empty. Invalidating cache.")
                self.remove(filename)
                return None
            logger.info(f"Loaded {len(df):,} rows from cache '{cache_file}'")
            return df
        except Exception as e:
            logger.warning(
                f"Corrupted or unreadable cache file '{cache_file}': {e}. Invalidating cache."
            )
            self.remove(filename)
            return None

    def remove(self, filename: str = "zomato_raw.parquet") -> bool:
        """
        Remove a specific cache file.

        Args:
            filename: Cache filename to delete.

        Returns:
            True if removed, False otherwise.
        """
        cache_file = self.get_path(filename)
        if cache_file.exists():
            try:
                cache_file.unlink()
                logger.info(f"Removed cache file '{cache_file}'")
                return True
            except OSError as e:
                logger.warning(f"Failed to remove cache file '{cache_file}': {e}")
                return False
        return False

    def clear(self) -> int:
        """
        Remove all cache files within the cache directory.

        Returns:
            Number of files removed.
        """
        if not self.cache_dir.exists():
            return 0

        count = 0
        for item in self.cache_dir.glob("*.parquet"):
            try:
                item.unlink()
                count += 1
            except OSError as e:
                logger.warning(f"Failed to remove cache file '{item}': {e}")

        logger.info(f"Cleared {count} cached files from '{self.cache_dir}'")
        return count
