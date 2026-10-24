"""
Logging setup for the Zomato AI Restaurant Recommendation System.

Provides a centralized logger factory with consistent formatting, configurable
log levels, and optional file output. All modules should use `get_logger(__name__)`
to get a properly namespaced logger instance.
"""

import logging
import sys
from pathlib import Path


# ── Module-level state ───────────────────────
_initialized: bool = False
_log_level: str = "INFO"


def setup_logging(
    level: str = "INFO",
    log_file: str | None = None,
    force: bool = False,
) -> None:
    """
    Initialize the logging system with consistent formatting.

    Should be called once at application startup. Subsequent calls
    update the log level, attach file logging if specified, and avoid duplicate handlers.

    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional path to a log file. If None, logs to console only.
        force: If True, remove existing handlers and reconfigure from scratch.
    """
    global _initialized, _log_level
    _log_level = level.upper()

    # Get the root logger for our application namespace
    root_logger = logging.getLogger("src")
    root_logger.setLevel(getattr(logging, _log_level, logging.INFO))

    if force:
        for handler in list(root_logger.handlers):
            root_logger.removeHandler(handler)
        _initialized = False

    # Avoid adding duplicate handlers on repeated calls
    if _initialized:
        # Just update the level
        root_logger.setLevel(getattr(logging, _log_level, logging.INFO))
        for handler in root_logger.handlers:
            handler.setLevel(getattr(logging, _log_level, logging.INFO))

        # Attach file handler if requested and not already present
        if log_file:
            log_path = Path(log_file).resolve()
            already_attached = any(
                isinstance(h, logging.FileHandler) and Path(h.baseFilename).resolve() == log_path
                for h in root_logger.handlers
            )
            if not already_attached:
                log_path.parent.mkdir(parents=True, exist_ok=True)
                file_handler = logging.FileHandler(log_path, encoding="utf-8")
                file_handler.setLevel(logging.DEBUG)
                file_formatter = logging.Formatter(
                    fmt="%(asctime)s | %(levelname)-8s | %(name)-35s | %(funcName)s:%(lineno)d | %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
                file_handler.setFormatter(file_formatter)
                root_logger.addHandler(file_handler)
        return

    # ── Console Handler ──
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, _log_level, logging.INFO))
    console_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # ── File Handler (optional) ──
    if log_file:
        log_path = Path(log_file).resolve()
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)  # File always captures everything
        file_formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)-35s | %(funcName)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Prevent logs from propagating to the root logger (avoids duplicates)
    root_logger.propagate = False

    _initialized = True



def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger instance for a module.

    If the logging system hasn't been initialized yet, it will be
    set up with default settings (INFO level, console only).

    Args:
        name: The module name, typically `__name__`.

    Returns:
        A configured Logger instance.

    Usage:
        from src.utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Data loaded successfully")
        logger.warning("Cache miss — downloading dataset")
        logger.error("LLM API call failed", exc_info=True)
    """
    if not _initialized:
        setup_logging(_log_level)

    logger = logging.getLogger(name)
    # If the logger is outside the 'src' hierarchy (e.g., '__main__', tests),
    # ensure it shares the application handlers and level so output is visible.
    if not name.startswith("src") and not logger.handlers:
        src_logger = logging.getLogger("src")
        for handler in src_logger.handlers:
            if handler not in logger.handlers:
                logger.addHandler(handler)
        logger.setLevel(src_logger.level)
        logger.propagate = False

    return logger

