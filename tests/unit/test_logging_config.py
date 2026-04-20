"""
Unit tests for centralized logging configuration.

Tests the logging_config module to ensure proper functionality:
- Basic setup
- Environment variable configuration
- JSON vs text formatting
- Production and development presets
- Logger retrieval
"""
import json
import logging
import os
import unittest
from io import StringIO
from unittest.mock import patch

from ingestion.logging_config import (
    setup_logging,
    get_logger,
    configure_for_production,
    configure_for_development,
    JsonFormatter,
    StandardFormatter,
)


class TestLoggingConfig(unittest.TestCase):
    """Test centralized logging configuration."""

    def setUp(self):
        """Reset logging before each test."""
        # Clear all handlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(logging.WARNING)

    def test_setup_logging_default(self):
        """Test default logging setup."""
        setup_logging()

        root_logger = logging.getLogger()
        self.assertEqual(root_logger.level, logging.INFO)
        self.assertEqual(len(root_logger.handlers), 1)

        handler = root_logger.handlers[0]
        self.assertIsInstance(handler.formatter, StandardFormatter)

    def test_setup_logging_custom_level(self):
        """Test logging setup with custom level."""
        setup_logging(level="DEBUG")

        root_logger = logging.getLogger()
        self.assertEqual(root_logger.level, logging.DEBUG)

    def test_setup_logging_json_format(self):
        """Test logging setup with JSON format."""
        setup_logging(json_format=True, force=True)

        root_logger = logging.getLogger()
        handler = root_logger.handlers[0]
        self.assertIsInstance(handler.formatter, JsonFormatter)

    def test_setup_logging_from_env(self):
        """Test logging setup from environment variables."""
        with patch.dict(os.environ, {"LOG_LEVEL": "WARNING", "LOG_JSON": "true"}):
            setup_logging(force=True)

            root_logger = logging.getLogger()
            self.assertEqual(root_logger.level, logging.WARNING)
            handler = root_logger.handlers[0]
            self.assertIsInstance(handler.formatter, JsonFormatter)

    def test_setup_logging_not_reconfigured(self):
        """Test that logging is not reconfigured unless forced."""
        setup_logging(level="INFO")
        setup_logging(level="DEBUG")  # Should be ignored

        root_logger = logging.getLogger()
        self.assertEqual(root_logger.level, logging.INFO)

    def test_setup_logging_force_reconfigure(self):
        """Test forced reconfiguration."""
        setup_logging(level="INFO")
        setup_logging(level="DEBUG", force=True)

        root_logger = logging.getLogger()
        self.assertEqual(root_logger.level, logging.DEBUG)

    def test_get_logger(self):
        """Test get_logger function."""
        logger = get_logger("test.module")

        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, "test.module")

    def test_configure_for_production(self):
        """Test production configuration preset."""
        configure_for_production()

        root_logger = logging.getLogger()
        self.assertEqual(root_logger.level, logging.INFO)
        handler = root_logger.handlers[0]
        self.assertIsInstance(handler.formatter, JsonFormatter)

    def test_configure_for_production_custom_level(self):
        """Test production configuration with custom level."""
        configure_for_production(level="WARNING")

        root_logger = logging.getLogger()
        self.assertEqual(root_logger.level, logging.WARNING)

    def test_configure_for_development(self):
        """Test development configuration preset."""
        configure_for_development()

        root_logger = logging.getLogger()
        self.assertEqual(root_logger.level, logging.DEBUG)
        handler = root_logger.handlers[0]
        self.assertIsInstance(handler.formatter, StandardFormatter)

    def test_json_formatter_basic(self):
        """Test JSON formatter with basic message."""
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        log_data = json.loads(output)

        self.assertEqual(log_data["level"], "INFO")
        self.assertEqual(log_data["logger"], "test")
        self.assertEqual(log_data["message"], "Test message")
        self.assertEqual(log_data["line"], 10)
        self.assertIn("timestamp", log_data)

    def test_json_formatter_with_extra(self):
        """Test JSON formatter with extra data."""
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.extra_data = {"key": "value", "count": 42}

        output = formatter.format(record)
        log_data = json.loads(output)

        self.assertEqual(log_data["extra"]["key"], "value")
        self.assertEqual(log_data["extra"]["count"], 42)

    def test_json_formatter_with_exception(self):
        """Test JSON formatter with exception."""
        formatter = JsonFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )

        output = formatter.format(record)
        log_data = json.loads(output)

        self.assertEqual(log_data["level"], "ERROR")
        self.assertIn("exception", log_data)
        self.assertIn("ValueError: Test error", log_data["exception"])

    def test_standard_formatter(self):
        """Test standard text formatter."""
        formatter = StandardFormatter()
        record = logging.LogRecord(
            name="test.module",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)

        self.assertIn("test.module", output)
        self.assertIn("INFO", output)
        self.assertIn("Test message", output)

    def test_logging_output_text_format(self):
        """Test actual logging output in text format."""
        # Capture stdout
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StandardFormatter())

        logger = logging.getLogger("test.output")
        logger.setLevel(logging.INFO)
        logger.handlers.clear()
        logger.addHandler(handler)

        logger.info("Test message")

        output = stream.getvalue()
        self.assertIn("test.output", output)
        self.assertIn("INFO", output)
        self.assertIn("Test message", output)

    def test_logging_output_json_format(self):
        """Test actual logging output in JSON format."""
        # Capture stdout
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(JsonFormatter())

        logger = logging.getLogger("test.json")
        logger.setLevel(logging.INFO)
        logger.handlers.clear()
        logger.addHandler(handler)

        logger.info("Test message", extra={"extra_data": {"key": "value"}})

        output = stream.getvalue()
        log_data = json.loads(output.strip())

        self.assertEqual(log_data["logger"], "test.json")
        self.assertEqual(log_data["level"], "INFO")
        self.assertEqual(log_data["message"], "Test message")
        self.assertEqual(log_data["extra"]["key"], "value")


class TestLoggingIntegration(unittest.TestCase):
    """Test logging integration with other modules."""

    def setUp(self):
        """Reset logging before each test."""
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(logging.WARNING)

    def test_import_from_ingestion_package(self):
        """Test importing logging utilities from ingestion package."""
        from ingestion import (
            setup_logging,
            get_logger,
            configure_for_production,
            configure_for_development,
        )

        # Should not raise any errors
        self.assertTrue(callable(setup_logging))
        self.assertTrue(callable(get_logger))
        self.assertTrue(callable(configure_for_production))
        self.assertTrue(callable(configure_for_development))

    def test_logger_hierarchy(self):
        """Test logger hierarchy and propagation."""
        setup_logging(level="INFO", force=True)

        parent_logger = get_logger("parent")
        child_logger = get_logger("parent.child")

        # Capture logs
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StandardFormatter())
        logging.getLogger().handlers[0] = handler

        child_logger.info("Child message")

        output = stream.getvalue()
        self.assertIn("parent.child", output)
        self.assertIn("Child message", output)

    def test_multiple_loggers(self):
        """Test multiple loggers from different modules."""
        setup_logging(force=True)

        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        self.assertIsNot(logger1, logger2)
        self.assertEqual(logger1.name, "module1")
        self.assertEqual(logger2.name, "module2")


if __name__ == "__main__":
    unittest.main()

