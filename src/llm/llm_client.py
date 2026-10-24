"""
LLM API client for Groq.

Provides resilient inference with exponential backoff retries, timeout management,
and structured JSON generation using Groq's high-speed inference engine.
"""

import os
import random
import time
from typing import Any
import groq
from groq import Groq

from src.utils.config import AppConfig
from src.utils.logger import get_logger

logger = get_logger(__name__)


class LLMError(Exception):
    """Base exception for LLM operations."""
    pass


class LLMAPIKeyError(LLMError):
    """Raised when the LLM API key is missing or invalid."""
    pass


class LLMRateLimitError(LLMError):
    """Raised when LLM rate limits are exceeded after all retries."""
    pass


class LLMClient:
    """
    Client for Groq LLM API.

    Features:
    - High-throughput inference powered by Groq LPU.
    - Exponential backoff with jitter on rate limits (HTTP 429) and timeouts.
    - Safe error handling distinguishing configuration errors from transient faults.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: int | None = None,
        max_retries: int | None = None,
        config: AppConfig | None = None,
    ) -> None:
        """
        Initialize LLMClient.

        Args:
            api_key: Groq API key. If omitted, loaded from config or GROQ_API_KEY env.
            model: Model name. Defaults to config.llm_model or 'llama-3.3-70b-versatile'.
            timeout_seconds: Timeout per request in seconds. Defaults to 30.
            max_retries: Maximum retry attempts for transient errors. Defaults to 3.
            config: Optional AppConfig instance.
        """
        self.config = config or AppConfig()
        self.api_key = (
            api_key
            if api_key is not None
            else self.config.primary_api_key or os.getenv("GROQ_API_KEY", "")
        )
        self.model = model or self.config.llm_model or "llama-3.3-70b-versatile"
        self.timeout = timeout_seconds if timeout_seconds is not None else self.config.llm_timeout_seconds
        self.max_retries = max_retries if max_retries is not None else self.config.llm_max_retries

        self._client: Groq | None = None

    @property
    def has_api_key(self) -> bool:
        """Check if a plausible API key is configured."""
        return bool(
            self.api_key
            and self.api_key not in ("your_groq_api_key_here", "your_api_key_here")
        )

    def _get_client(self) -> Groq:
        """Initialize or return cached Groq client."""
        if not self.has_api_key:
            raise LLMAPIKeyError(
                "Groq API key is not configured. Please set GROQ_API_KEY in your .env file."
            )

        if self._client is None:
            self._client = Groq(
                api_key=self.api_key,
                timeout=float(self.timeout),
            )
        return self._client

    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> str:
        """
        Send prompt to Groq and return raw response string.

        Args:
            prompt: Formatted user prompt.
            temperature: Sampling temperature (0.0 to 2.0).
            max_tokens: Maximum tokens in response.
            json_mode: If True, requests JSON object format from the model.

        Returns:
            str: Raw LLM response text.

        Raises:
            LLMAPIKeyError: If API key is missing.
            LLMRateLimitError: If rate limit persists across retries.
            LLMError: For fatal API failures or network errors.
        """
        client = self._get_client()

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert restaurant recommendation engine. "
                    "Analyze diner preferences and return structured recommendations."
                ),
            },
            {"role": "user", "content": prompt},
        ]

        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        backoff = 1.0
        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                logger.info(
                    f"Calling Groq API (model: '{self.model}', attempt {attempt + 1}/{self.max_retries + 1})..."
                )
                response = client.chat.completions.create(**kwargs)
                content = response.choices[0].message.content
                if content is None:
                    raise LLMError("Groq API returned empty message content.")
                return content

            except groq.RateLimitError as exc:
                last_error = exc
                if attempt < self.max_retries:
                    sleep_time = backoff + random.uniform(0.1, 0.5)
                    logger.warning(
                        f"Groq rate limit hit (HTTP 429). Retrying in {sleep_time:.2f}s "
                        f"(attempt {attempt + 1}/{self.max_retries})..."
                    )
                    time.sleep(sleep_time)
                    backoff *= 2.0
                else:
                    raise LLMRateLimitError(
                        f"Groq rate limit exceeded after {self.max_retries} retries."
                    ) from exc

            except (groq.APITimeoutError, groq.APIConnectionError, groq.InternalServerError) as exc:
                last_error = exc
                if attempt < self.max_retries:
                    sleep_time = backoff + random.uniform(0.1, 0.5)
                    logger.warning(
                        f"Groq API transient error ({type(exc).__name__}): {exc}. "
                        f"Retrying in {sleep_time:.2f}s (attempt {attempt + 1}/{self.max_retries})..."
                    )
                    time.sleep(sleep_time)
                    backoff *= 2.0
                else:
                    raise LLMError(
                        f"Groq API call failed after {self.max_retries} retries: {exc}"
                    ) from exc

            except groq.AuthenticationError as exc:
                raise LLMAPIKeyError(f"Invalid Groq API key: {exc}") from exc

            except Exception as exc:
                raise LLMError(f"Unexpected error during Groq API call: {exc}") from exc

        raise LLMError(f"Failed to generate response: {last_error}")
