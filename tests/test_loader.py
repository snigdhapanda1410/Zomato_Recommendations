"""
Unit tests for DatasetLoader and DatasetCache.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pandas as pd
import pytest

from src.data.cache import DatasetCache
from src.data.loader import DatasetEmptyError, DatasetLoader, DatasetLoadError
from src.utils.config import AppConfig


@pytest.fixture
def sample_raw_df() -> pd.DataFrame:
    """Fixture providing a mock raw DataFrame matching HF schema."""
    return pd.DataFrame({
        "url": ["https://zomato.com/1", "https://zomato.com/2"],
        "address": ["123 Main St", "456 Side St"],
        "name": ["Test Cafe", "Spice Hub"],
        "online_order": ["Yes", "No"],
        "book_table": ["No", "Yes"],
        "rate": ["4.1/5", "3.8/5"],
        "votes": [120, 450],
        "phone": ["1234567890", "0987654321"],
        "location": ["Koramangala", "Indiranagar"],
        "rest_type": ["Cafe", "Casual Dining"],
        "dish_liked": ["Coffee", "Biryani"],
        "cuisines": ["Cafe, Desserts", "North Indian, Mughlai"],
        "approx_cost(for two people)": ["600", "1,200"],
        "reviews_list": ["[]", "[]"],
        "menu_item": ["[]", "[]"],
        "listed_in(type)": ["Dine-out", "Dine-out"],
        "listed_in(city)": ["Koramangala", "Indiranagar"],
    })


# ── DatasetCache Tests ──────────────────────────────────────────


def test_cache_save_and_load(tmp_path: Path, sample_raw_df: pd.DataFrame):
    """Verify that saving and loading via DatasetCache preserves DataFrame."""
    cache = DatasetCache(cache_dir=tmp_path)
    filename = "test_data.parquet"

    assert not cache.exists(filename)
    saved_path = cache.save(sample_raw_df, filename)

    assert saved_path is not None
    assert saved_path.exists()
    assert cache.exists(filename)

    loaded_df = cache.load(filename)
    assert loaded_df is not None
    assert len(loaded_df) == len(sample_raw_df)
    assert list(loaded_df.columns) == list(sample_raw_df.columns)


def test_cache_load_nonexistent(tmp_path: Path):
    """Verify loading a nonexistent file returns None."""
    cache = DatasetCache(cache_dir=tmp_path)
    assert cache.load("missing.parquet") is None


def test_cache_save_empty_returns_none(tmp_path: Path):
    """Verify attempting to save an empty DataFrame returns None."""
    cache = DatasetCache(cache_dir=tmp_path)
    empty_df = pd.DataFrame()
    assert cache.save(empty_df, "empty.parquet") is None


def test_cache_handles_corrupt_file(tmp_path: Path):
    """Verify that a corrupted parquet file is safely removed and returns None."""
    cache = DatasetCache(cache_dir=tmp_path)
    corrupt_file = tmp_path / "corrupt.parquet"
    corrupt_file.write_text("This is not a valid parquet file")

    assert corrupt_file.exists()
    loaded_df = cache.load("corrupt.parquet")
    assert loaded_df is None
    # Corrupt file should have been deleted (invalidation)
    assert not corrupt_file.exists()


def test_cache_clear(tmp_path: Path, sample_raw_df: pd.DataFrame):
    """Verify clearing all parquet files in cache directory."""
    cache = DatasetCache(cache_dir=tmp_path)
    cache.save(sample_raw_df, "f1.parquet")
    cache.save(sample_raw_df, "f2.parquet")

    assert (tmp_path / "f1.parquet").exists()
    assert (tmp_path / "f2.parquet").exists()

    removed = cache.clear()
    assert removed == 2
    assert not (tmp_path / "f1.parquet").exists()
    assert not (tmp_path / "f2.parquet").exists()


# ── DatasetLoader Tests ─────────────────────────────────────────


def test_loader_uses_cache_when_available(tmp_path: Path, sample_raw_df: pd.DataFrame):
    """Verify loader skips remote fetch when cache is populated."""
    config = AppConfig(cache_dir=tmp_path, cache_enabled=True)
    cache = DatasetCache(cache_dir=tmp_path)
    cache.save(sample_raw_df, "zomato_raw.parquet")

    loader = DatasetLoader(config=config, cache=cache)

    with patch.object(loader, "_fetch_from_huggingface") as mock_fetch:
        df = loader.load(force_download=False)
        mock_fetch.assert_not_called()
        assert len(df) == 2


def test_loader_force_download_bypasses_cache(tmp_path: Path, sample_raw_df: pd.DataFrame):
    """Verify force_download=True invokes remote fetch even if cache exists."""
    config = AppConfig(cache_dir=tmp_path, cache_enabled=True)
    cache = DatasetCache(cache_dir=tmp_path)
    cache.save(sample_raw_df, "zomato_raw.parquet")

    loader = DatasetLoader(config=config, cache=cache)

    with patch.object(loader, "_fetch_from_huggingface", return_value=sample_raw_df) as mock_fetch:
        df = loader.load(force_download=True)
        mock_fetch.assert_called_once()
        assert len(df) == 2


def test_loader_cache_disabled_fetches_remote(tmp_path: Path, sample_raw_df: pd.DataFrame):
    """Verify cache_enabled=False fetches from remote without reading cache."""
    config = AppConfig(cache_dir=tmp_path, cache_enabled=False)
    cache = DatasetCache(cache_dir=tmp_path)
    cache.save(sample_raw_df, "zomato_raw.parquet")

    loader = DatasetLoader(config=config, cache=cache)

    with patch.object(loader, "_fetch_from_huggingface", return_value=sample_raw_df) as mock_fetch:
        df = loader.load()
        mock_fetch.assert_called_once()
        assert len(df) == 2


def test_loader_network_failure_falls_back_to_cache(tmp_path: Path, sample_raw_df: pd.DataFrame):
    """Verify network error triggers fallback to cache if available (DI-01, DI-06)."""
    config = AppConfig(cache_dir=tmp_path, cache_enabled=True)
    cache = DatasetCache(cache_dir=tmp_path)
    cache.save(sample_raw_df, "zomato_raw.parquet")

    loader = DatasetLoader(config=config, cache=cache)

    with patch.object(loader, "_fetch_from_huggingface", side_effect=ConnectionError("HF down")):
        df = loader.load(force_download=True)
        assert len(df) == 2


def test_loader_network_failure_raises_when_no_cache(tmp_path: Path):
    """Verify network error raises DatasetLoadError when no cache exists."""
    config = AppConfig(cache_dir=tmp_path, cache_enabled=True)
    cache = DatasetCache(cache_dir=tmp_path)
    loader = DatasetLoader(config=config, cache=cache)

    with patch.object(loader, "_fetch_from_huggingface", side_effect=ConnectionError("HF down")):
        with pytest.raises(DatasetLoadError, match="Failed to download dataset"):
            loader.load()


def test_loader_empty_dataset_raises(tmp_path: Path):
    """Verify 0-row dataset raises DatasetEmptyError (DI-03)."""
    config = AppConfig(cache_dir=tmp_path)
    loader = DatasetLoader(config=config)
    empty_df = pd.DataFrame()

    with patch.object(loader, "_fetch_from_huggingface", return_value=empty_df):
        with pytest.raises(DatasetEmptyError, match="Dataset is empty"):
            loader.load()


def test_loader_schema_missing_columns_raises(tmp_path: Path):
    """Verify missing required columns raises DatasetLoadError (DI-02)."""
    config = AppConfig(cache_dir=tmp_path)
    loader = DatasetLoader(config=config)
    invalid_df = pd.DataFrame({"name": ["Place A"], "other_col": [1]})

    with patch.object(loader, "_fetch_from_huggingface", return_value=invalid_df):
        with pytest.raises(DatasetLoadError, match="missing required columns"):
            loader.load()
