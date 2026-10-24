"""
Unit tests for logging setup (setup_logging, get_logger).
"""

import logging
from pathlib import Path
import pytest
from src.utils.logger import get_logger, setup_logging


def test_get_logger_creation():
    """Verify that get_logger returns a Logger with correct name."""
    logger = get_logger("src.test_module")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "src.test_module"


def test_get_logger_non_src_module():
    """Verify that get_logger configures non-src loggers properly (like __main__)."""
    logger = get_logger("__main__")
    assert isinstance(logger, logging.Logger)
    assert len(logger.handlers) > 0


def test_setup_logging_file(tmp_path):
    """Verify that setup_logging properly adds file handler when requested."""
    log_file = tmp_path / "test.log"
    setup_logging(level="DEBUG", log_file=str(log_file))

    logger = get_logger("src.file_test")
    logger.info("Test message for log file")

    # Flush handlers
    for handler in logging.getLogger("src").handlers:
        handler.flush()

    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "Test message for log file" in content
