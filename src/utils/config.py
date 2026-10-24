"""
Configuration management for the Zomato AI Restaurant Recommendation System.

Loads environment variables from a .env file and provides a centralized
AppConfig dataclass with validation and sensible defaults for all settings.
"""

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


def _find_env_file() -> Path | None:
    """Search for .env file starting from the project root."""
    # Walk up from this file's location to find the project root .env
    current = Path(__file__).resolve().parent
    for _ in range(5):  # max 5 levels up
        env_path = current / ".env"
        if env_path.exists():
            return env_path
        current = current.parent
    return None


@dataclass
class AppConfig:
    """
    Centralized application configuration.

    Loads values from environment variables (via .env file) with validation
    and sensible defaults. Required fields (like GEMINI_API_KEY) will raise
    a clear error if missing.

    Usage:
        config = AppConfig()
        print(config.llm_model)        # "gemini-2.0-flash"
        print(config.budget_low_max)   # 400
    """

    # ── LLM Configuration ────────────────────────
    groq_api_key: str = ""
    gemini_api_key: str = ""
    llm_model: str = "llama-3.3-70b-versatile"
    llm_temperature: float = 0.7
    llm_max_retries: int = 3
    llm_timeout_seconds: int = 30

    # ── Dataset Configuration ────────────────────
    dataset_name: str = "ManikaSaini/zomato-restaurant-recommendation"
    cache_dir: Path = field(default_factory=lambda: Path("./data/cache"))
    cache_enabled: bool = True

    # ── Budget Thresholds (₹, for two) ──────────
    budget_low_max: int = 400
    budget_medium_max: int = 1000

    # ── Application ──────────────────────────────
    top_n_recommendations: int = 5
    max_restaurants_to_llm: int = 50
    log_level: str = "INFO"

    def __init__(
        self,
        groq_api_key: str | None = None,
        gemini_api_key: str | None = None,
        llm_model: str | None = None,
        llm_temperature: float | None = None,
        llm_max_retries: int | None = None,
        llm_timeout_seconds: int | None = None,
        dataset_name: str | None = None,
        cache_dir: Path | str | None = None,
        cache_enabled: bool | None = None,
        budget_low_max: int | None = None,
        budget_medium_max: int | None = None,
        top_n_recommendations: int | None = None,
        max_restaurants_to_llm: int | None = None,
        log_level: str | None = None,
    ) -> None:
        """Initialize AppConfig, giving precedence to explicit args over .env."""
        env_path = _find_env_file()
        if env_path:
            load_dotenv(env_path)

        # ── LLM ──
        self.groq_api_key = (
            groq_api_key if groq_api_key is not None else os.getenv("GROQ_API_KEY", "")
        )
        self.gemini_api_key = (
            gemini_api_key
            if gemini_api_key is not None
            else os.getenv("GEMINI_API_KEY", "")
        )
        self.llm_model = (
            llm_model
            if llm_model is not None
            else os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
        )
        self.llm_temperature = (
            float(llm_temperature)
            if llm_temperature is not None
            else float(os.getenv("LLM_TEMPERATURE", "0.7"))
        )
        self.llm_max_retries = (
            int(llm_max_retries)
            if llm_max_retries is not None
            else int(os.getenv("LLM_MAX_RETRIES", "3"))
        )
        self.llm_timeout_seconds = (
            int(llm_timeout_seconds)
            if llm_timeout_seconds is not None
            else int(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
        )

        # ── Dataset ──
        self.dataset_name = (
            dataset_name
            if dataset_name is not None
            else os.getenv(
                "DATASET_NAME", "ManikaSaini/zomato-restaurant-recommendation"
            )
        )
        self.cache_dir = (
            Path(cache_dir)
            if cache_dir is not None
            else Path(os.getenv("CACHE_DIR", "./data/cache"))
        )
        if cache_enabled is not None:
            self.cache_enabled = bool(cache_enabled)
        else:
            self.cache_enabled = os.getenv("CACHE_ENABLED", "true").lower() in (
                "true",
                "1",
                "yes",
            )

        # ── Budget Thresholds ──
        self.budget_low_max = (
            int(budget_low_max)
            if budget_low_max is not None
            else int(os.getenv("BUDGET_LOW_MAX", "400"))
        )
        self.budget_medium_max = (
            int(budget_medium_max)
            if budget_medium_max is not None
            else int(os.getenv("BUDGET_MEDIUM_MAX", "1000"))
        )

        # ── Application ──
        self.top_n_recommendations = (
            int(top_n_recommendations)
            if top_n_recommendations is not None
            else int(os.getenv("TOP_N_RECOMMENDATIONS", "5"))
        )
        self.max_restaurants_to_llm = (
            int(max_restaurants_to_llm)
            if max_restaurants_to_llm is not None
            else int(os.getenv("MAX_RESTAURANTS_TO_LLM", "50"))
        )
        self.log_level = (
            log_level.upper().strip()
            if log_level is not None
            else os.getenv("LOG_LEVEL", "INFO").upper().strip()
        )

        self._validate()

    def _validate(self) -> None:
        """Validate configuration values and warn about issues."""
        errors: list[str] = []
        warnings: list[str] = []

        # ── Required fields ──
        has_any_key = (
            (self.groq_api_key and self.groq_api_key != "your_groq_api_key_here")
            or (self.gemini_api_key and self.gemini_api_key != "your_api_key_here")
        )
        if not has_any_key:
            warnings.append(
                "GROQ_API_KEY (or GEMINI_API_KEY) is not set. LLM features will use fallback mode. "
                "Set it in your .env file (copy .env.example to .env)."
            )

        # ── Value range checks ──
        if not (0.0 <= self.llm_temperature <= 2.0):
            warnings.append(
                f"LLM_TEMPERATURE={self.llm_temperature} is outside [0.0, 2.0]. "
                f"Clamping to valid range."
            )
            self.llm_temperature = max(0.0, min(2.0, self.llm_temperature))

        if self.llm_max_retries < 0:
            self.llm_max_retries = 0

        if self.llm_timeout_seconds < 1:
            warnings.append("LLM_TIMEOUT_SECONDS must be ≥ 1. Setting to 30.")
            self.llm_timeout_seconds = 30

        if self.budget_low_max <= 0:
            warnings.append("BUDGET_LOW_MAX must be > 0. Using default 400.")
            self.budget_low_max = 400

        if self.budget_medium_max <= self.budget_low_max:
            warnings.append(
                f"BUDGET_MEDIUM_MAX ({self.budget_medium_max}) must be > "
                f"BUDGET_LOW_MAX ({self.budget_low_max}). Using default 1000."
            )
            self.budget_medium_max = 1000

        if self.top_n_recommendations < 1:
            warnings.append("TOP_N_RECOMMENDATIONS must be ≥ 1. Using default 5.")
            self.top_n_recommendations = 5

        if self.max_restaurants_to_llm < 1:
            warnings.append("MAX_RESTAURANTS_TO_LLM must be ≥ 1. Using default 50.")
            self.max_restaurants_to_llm = 50
        elif self.max_restaurants_to_llm > 100:
            warnings.append(
                f"MAX_RESTAURANTS_TO_LLM={self.max_restaurants_to_llm} is very high. "
                f"This may exceed LLM context window. Capping at 100."
            )
            self.max_restaurants_to_llm = 100

        valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.log_level not in valid_log_levels:
            warnings.append(
                f"LOG_LEVEL='{self.log_level}' is invalid. Using 'INFO'."
            )
            self.log_level = "INFO"

        # ── Print warnings to stderr ──
        for warning in warnings:
            print(f"[Config Warning] {warning}", file=sys.stderr)

        # ── Raise on critical errors ──
        if errors:
            raise ValueError(
                "Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors)
            )

    @property
    def has_api_key(self) -> bool:
        """Check if a valid API key is configured (Groq or Gemini)."""
        return bool(
            (self.groq_api_key and self.groq_api_key != "your_groq_api_key_here")
            or (self.gemini_api_key and self.gemini_api_key != "your_api_key_here")
        )

    @property
    def primary_api_key(self) -> str:
        """Get the active API key (prefers Groq)."""
        if self.groq_api_key and self.groq_api_key != "your_groq_api_key_here":
            return self.groq_api_key
        return self.gemini_api_key

    def __repr__(self) -> str:
        """Safe repr that masks API keys."""
        groq_display = "***" if (self.groq_api_key and self.groq_api_key != "your_groq_api_key_here") else "(not set)"
        return (
            f"AppConfig(\n"
            f"  groq_api_key={groq_display},\n"
            f"  llm_model='{self.llm_model}',\n"
            f"  llm_temperature={self.llm_temperature},\n"
            f"  dataset_name='{self.dataset_name}',\n"
            f"  cache_dir='{self.cache_dir}',\n"
            f"  budget_low_max={self.budget_low_max},\n"
            f"  budget_medium_max={self.budget_medium_max},\n"
            f"  top_n_recommendations={self.top_n_recommendations},\n"
            f"  log_level='{self.log_level}'\n"
            f")"
        )
