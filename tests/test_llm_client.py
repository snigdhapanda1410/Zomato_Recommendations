"""
Unit tests for LLMClient and Groq integration.
"""

from unittest.mock import MagicMock, patch
import groq
import pytest

from src.llm.llm_client import LLMAPIKeyError, LLMClient, LLMError, LLMRateLimitError


def test_llm_client_missing_key_raises():
    """Verify initializing and calling without key raises LLMAPIKeyError."""
    client = LLMClient(api_key="")
    with pytest.raises(LLMAPIKeyError, match="Groq API key is not configured"):
        client.generate("Test prompt")


def test_llm_client_placeholder_key_raises():
    """Verify placeholder keys raise LLMAPIKeyError."""
    client = LLMClient(api_key="your_groq_api_key_here")
    with pytest.raises(LLMAPIKeyError, match="Groq API key is not configured"):
        client.generate("Test prompt")


def test_llm_client_successful_generation():
    """Verify successful generation calls groq client and returns content."""
    client = LLMClient(api_key="gsk_valid_test_key", model="llama-3.3-70b-versatile")

    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = '[{"restaurant_name": "Truffles"}]'
    mock_response.choices = [mock_choice]

    with patch("src.llm.llm_client.Groq") as mock_groq_class:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create.return_value = mock_response
        mock_groq_class.return_value = mock_instance

        output = client.generate("Recommend restaurants")
        assert output == '[{"restaurant_name": "Truffles"}]'
        mock_instance.chat.completions.create.assert_called_once()


def test_llm_client_rate_limit_retry_success():
    """Verify client retries upon RateLimitError and succeeds on subsequent attempt."""
    client = LLMClient(api_key="gsk_valid_test_key", max_retries=2)

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Success after retry"))]

    # Create mock response object for RateLimitError
    fake_response = MagicMock()
    fake_response.status_code = 429
    fake_response.headers = {}
    rate_err = groq.RateLimitError(
        message="Rate limit reached",
        response=fake_response,
        body={"error": {"message": "Rate limit reached"}},
    )

    with patch("src.llm.llm_client.Groq") as mock_groq_class:
        mock_instance = MagicMock()
        # 1st attempt fails with RateLimitError, 2nd succeeds
        mock_instance.chat.completions.create.side_effect = [rate_err, mock_response]
        mock_groq_class.return_value = mock_instance

        with patch("time.sleep") as mock_sleep:
            output = client.generate("Prompt")
            assert output == "Success after retry"
            assert mock_instance.chat.completions.create.call_count == 2
            mock_sleep.assert_called_once()


def test_llm_client_rate_limit_exceeded_raises():
    """Verify LLMRateLimitError is raised when retries are exhausted."""
    client = LLMClient(api_key="gsk_valid_test_key", max_retries=1)

    fake_response = MagicMock()
    fake_response.status_code = 429
    fake_response.headers = {}
    rate_err = groq.RateLimitError(
        message="Rate limit reached",
        response=fake_response,
        body={},
    )

    with patch("src.llm.llm_client.Groq") as mock_groq_class:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create.side_effect = rate_err
        mock_groq_class.return_value = mock_instance

        with patch("time.sleep"):
            with pytest.raises(LLMRateLimitError, match="Groq rate limit exceeded"):
                client.generate("Prompt")


def test_llm_client_authentication_error_raises_immediately():
    """Verify AuthenticationError raises LLMAPIKeyError without retrying."""
    client = LLMClient(api_key="gsk_invalid_key", max_retries=3)

    fake_response = MagicMock()
    fake_response.status_code = 401
    auth_err = groq.AuthenticationError(
        message="Invalid API Key",
        response=fake_response,
        body={},
    )

    with patch("src.llm.llm_client.Groq") as mock_groq_class:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create.side_effect = auth_err
        mock_groq_class.return_value = mock_instance

        with patch("time.sleep") as mock_sleep:
            with pytest.raises(LLMAPIKeyError, match="Invalid Groq API key"):
                client.generate("Prompt")
            # Should fail fast without retry sleep
            mock_sleep.assert_not_called()
