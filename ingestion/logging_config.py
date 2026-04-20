"""
Centralized logging configuration for the GitHub Archive Data Pipeline.

This module provides consistent logging setup across all components:
- Core ingestion modules
- Examples
- DAGs
- Tests

Usage:
    from ingestion.logging_config import setup_logging, get_logger

    # Setup logging (call once at application startup)
    setup_logging()

    # Get logger in any module
    logger = get_logger(__name__)
    logger.info("Processing started")

Features:
- Environment-based configuration (LOG_LEVEL, LOG_FORMAT, LOG_JSON)
- Structured JSON logging for production
- Consistent format across all modules
- Proper exception logging
"""
import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Optional


class JsonFormatter(logging.Formatter):
    """
    Format logs as JSON for production systems.

    Output format:
    {
        "timestamp": "2026-04-20T10:30:45.123456+00:00",
        "level": "INFO",
        "logger": "ingestion.github_archive_client",
        "message": "Downloading events",
        "module": "github_archive_client",
        "function": "download_events",
        "line": 109,
        "extra": {...}
    }
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data

        return json.dumps(log_data)


class StandardFormatter(logging.Formatter):
    """
    Standard text formatter for development.

    Output format:
    2026-04-20 10:30:45,123 - ingestion.github_archive_client - INFO - Downloading events
    """

    def __init__(self):
        """Initialize with default format."""
        super().__init__(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )


def setup_logging(
    level: Optional[str] = None,
    json_format: Optional[bool] = None,
    force: bool = False,
) -> None:
    """
    Configure logging for the entire application.

    This should be called once at application startup. Subsequent calls
    will be ignored unless force=True.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               If None, reads from LOG_LEVEL env var (default: INFO)
        json_format: Use JSON format for logs. If None, reads from LOG_JSON
                    env var (default: False)
        force: Force reconfiguration even if already configured

    Environment Variables:
        LOG_LEVEL: Logging level (default: INFO)
        LOG_JSON: Enable JSON format (true/false, default: false)

    Examples:
        # Use environment variables
        setup_logging()

        # Override with explicit values
        setup_logging(level="DEBUG", json_format=True)

        # Force reconfiguration
        setup_logging(force=True)
    """
    # Check if already configured
    root_logger = logging.getLogger()
    if root_logger.handlers and not force:
        return

    # Determine log level
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level, logging.INFO)

    # Determine log format
    if json_format is None:
        json_format = os.getenv("LOG_JSON", "false").lower() == "true"

    # Configure root logger
    root_logger.setLevel(level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    # Set formatter
    if json_format:
        formatter = JsonFormatter()
    else:
        formatter = StandardFormatter()

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Log configuration
    root_logger.info(
        f"Logging configured: level={logging.getLevelName(level)}, "
        f"format={'JSON' if json_format else 'TEXT'}"
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given name.

    This is a convenience wrapper around logging.getLogger() that ensures
    logging is configured before returning the logger.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance

    Example:
        logger = get_logger(__name__)
        logger.info("Processing started")
    """
    # Ensure logging is configured
    setup_logging()
    return logging.getLogger(name)


def configure_for_production(level: str = "INFO") -> None:
    """
    Configure logging for production environment.

    Sets up:
    - JSON formatted logs
    - Appropriate log level
    - UTF-8 encoding

    Args:
        level: Log level (default: INFO)

    Example:
        from ingestion.logging_config import configure_for_production
        configure_for_production(level="WARNING")
    """
    setup_logging(level=level, json_format=True, force=True)


def configure_for_development(level: str = "DEBUG") -> None:
    """
    Configure logging for development environment.

    Sets up:
    - Human-readable text format
    - Debug level logging

    Args:
        level: Log level (default: DEBUG)

    Example:
        from ingestion.logging_config import configure_for_development
        configure_for_development()
    """
    setup_logging(level=level, json_format=False, force=True)


# Auto-configure on import if not already configured
# This ensures logging works even if setup_logging() is not explicitly called
setup_logging()

