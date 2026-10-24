"""
Unit tests for configuration management (AppConfig).
"""

import os
from pathlib import Path
import pytest
from src.utils.config import AppConfig, _find_env_file


def test_app_config_defaults():
    """Verify default configuration values."""
    config = AppConfig()
    assert config.llm_model in ("llama-3.3-70b-versatile", "openai/gpt-oss-120b")
    assert config.llm_temperature == 0.7
    assert config.llm_max_retries == 3
    assert config.llm_timeout_seconds == 30
    assert config.dataset_name == "ManikaSaini/zomato-restaurant-recommendation"
    assert config.cache_enabled is True
    assert config.budget_low_max == 400
    assert config.budget_medium_max == 1000
    assert config.top_n_recommendations == 5
    assert config.max_restaurants_to_llm == 50
    assert config.log_level == "INFO"


def test_app_config_env_override(monkeypatch):
    """Verify that environment variables correctly override defaults."""
    monkeypatch.setenv("LLM_MODEL", "llama-3.1-8b-instant")
    monkeypatch.setenv("LLM_TEMPERATURE", "0.2")
    monkeypatch.setenv("LLM_MAX_RETRIES", "5")
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "45")
    monkeypatch.setenv("BUDGET_LOW_MAX", "500")
    monkeypatch.setenv("BUDGET_MEDIUM_MAX", "1200")
    monkeypatch.setenv("TOP_N_RECOMMENDATIONS", "10")
    monkeypatch.setenv("MAX_RESTAURANTS_TO_LLM", "30")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test-secret-key-123")
    monkeypatch.setenv("CACHE_ENABLED", "false")

    config = AppConfig()
    assert config.llm_model == "llama-3.1-8b-instant"
    assert config.llm_temperature == 0.2
    assert config.llm_max_retries == 5
    assert config.llm_timeout_seconds == 45
    assert config.budget_low_max == 500
    assert config.budget_medium_max == 1200
    assert config.top_n_recommendations == 10
    assert config.max_restaurants_to_llm == 30
    assert config.log_level == "DEBUG"
    assert config.groq_api_key == "gsk_test-secret-key-123"
    assert config.primary_api_key == "gsk_test-secret-key-123"
    assert config.cache_enabled is False
    assert config.has_api_key is True


def test_app_config_repr_masks_api_key(monkeypatch):
    """Ensure API key is masked in string representation."""
    monkeypatch.setenv("GROQ_API_KEY", "secret-groq-key-value")
    config = AppConfig()
    repr_str = repr(config)
    assert "secret-groq-key-value" not in repr_str
    assert "***" in repr_str


def test_app_config_clamping_and_fallback(monkeypatch):
    """Ensure invalid/out-of-range values are clamped or defaulted with warnings."""
    monkeypatch.setenv("LLM_TEMPERATURE", "3.5")  # > 2.0
    monkeypatch.setenv("LLM_MAX_RETRIES", "-2")
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "0")
    monkeypatch.setenv("BUDGET_LOW_MAX", "-50")
    monkeypatch.setenv("BUDGET_MEDIUM_MAX", "300")  # less than low
    monkeypatch.setenv("TOP_N_RECOMMENDATIONS", "0")
    monkeypatch.setenv("MAX_RESTAURANTS_TO_LLM", "200")  # > 100
    monkeypatch.setenv("LOG_LEVEL", "UNKNOWN_LEVEL")

    config = AppConfig()
    assert config.llm_temperature == 2.0
    assert config.llm_max_retries == 0
    assert config.llm_timeout_seconds == 30
    assert config.budget_low_max == 400
    assert config.budget_medium_max == 1000
    assert config.top_n_recommendations == 5
    assert config.max_restaurants_to_llm == 100
    assert config.log_level == "INFO"
