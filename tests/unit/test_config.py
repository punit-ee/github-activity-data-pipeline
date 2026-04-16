"""Unit tests for configuration management."""
import os
import unittest
from unittest.mock import patch

from ingestion.config import (
    GitHubArchiveConfig,
    DownloadConfig,
    LoggingConfig,
    PipelineConfig,
)


class TestGitHubArchiveConfig(unittest.TestCase):
    """Test GitHubArchiveConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = GitHubArchiveConfig()

        self.assertEqual(config.connect_timeout, 5.0)
        self.assertEqual(config.read_timeout, 30.0)
        self.assertEqual(config.max_retries, 3)
        self.assertEqual(config.retry_backoff_factor, 0.5)
        self.assertEqual(config.base_url, "https://data.gharchive.org")
        self.assertEqual(config.user_agent, "github-activity-data-pipeline/1.0")

    def test_timeout_property(self):
        """Test timeout property returns tuple."""
        config = GitHubArchiveConfig(connect_timeout=10.0, read_timeout=60.0)

        self.assertEqual(config.timeout, (10.0, 60.0))

    def test_from_env(self):
        """Test creating config from environment variables."""
        env_vars = {
            "GITHUB_ARCHIVE_CONNECT_TIMEOUT": "15.0",
            "GITHUB_ARCHIVE_READ_TIMEOUT": "90.0",
            "GITHUB_ARCHIVE_MAX_RETRIES": "5",
            "GITHUB_ARCHIVE_USER_AGENT": "custom-agent/1.0",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config = GitHubArchiveConfig.from_env()

            self.assertEqual(config.connect_timeout, 15.0)
            self.assertEqual(config.read_timeout, 90.0)
            self.assertEqual(config.max_retries, 5)
            self.assertEqual(config.user_agent, "custom-agent/1.0")

    def test_validate_success(self):
        """Test validation passes for valid config."""
        config = GitHubArchiveConfig()
        config.validate()  # Should not raise

    def test_validate_negative_timeout(self):
        """Test validation fails for negative timeout."""
        config = GitHubArchiveConfig(connect_timeout=-1.0)

        with self.assertRaises(ValueError) as ctx:
            config.validate()

        self.assertIn("connect_timeout must be positive", str(ctx.exception))

    def test_validate_empty_base_url(self):
        """Test validation fails for empty base URL."""
        config = GitHubArchiveConfig(base_url="")

        with self.assertRaises(ValueError) as ctx:
            config.validate()

        self.assertIn("base_url cannot be empty", str(ctx.exception))


class TestDownloadConfig(unittest.TestCase):
    """Test DownloadConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = DownloadConfig()

        self.assertEqual(config.chunk_size, 1024 * 1024)
        self.assertEqual(config.max_workers, 3)
        self.assertEqual(config.output_dir, "./data")
        self.assertFalse(config.overwrite_existing)

    def test_from_env(self):
        """Test creating config from environment variables."""
        env_vars = {
            "DOWNLOAD_CHUNK_SIZE": "2097152",  # 2MB
            "DOWNLOAD_MAX_WORKERS": "5",
            "DOWNLOAD_OUTPUT_DIR": "/tmp/data",
            "DOWNLOAD_OVERWRITE": "true",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config = DownloadConfig.from_env()

            self.assertEqual(config.chunk_size, 2097152)
            self.assertEqual(config.max_workers, 5)
            self.assertEqual(config.output_dir, "/tmp/data")
            self.assertTrue(config.overwrite_existing)


class TestLoggingConfig(unittest.TestCase):
    """Test LoggingConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = LoggingConfig()

        self.assertEqual(config.level, "INFO")
        self.assertFalse(config.json_format)

    def test_from_env(self):
        """Test creating config from environment variables."""
        env_vars = {
            "LOG_LEVEL": "DEBUG",
            "LOG_JSON": "true",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config = LoggingConfig.from_env()

            self.assertEqual(config.level, "DEBUG")
            self.assertTrue(config.json_format)


class TestPipelineConfig(unittest.TestCase):
    """Test PipelineConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = PipelineConfig()

        self.assertIsInstance(config.github_archive, GitHubArchiveConfig)
        self.assertIsInstance(config.download, DownloadConfig)
        self.assertIsInstance(config.logging, LoggingConfig)

    def test_from_env(self):
        """Test creating complete config from environment."""
        env_vars = {
            "GITHUB_ARCHIVE_CONNECT_TIMEOUT": "20.0",
            "DOWNLOAD_MAX_WORKERS": "10",
            "LOG_LEVEL": "WARNING",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config = PipelineConfig.from_env()

            self.assertEqual(config.github_archive.connect_timeout, 20.0)
            self.assertEqual(config.download.max_workers, 10)
            self.assertEqual(config.logging.level, "WARNING")

    def test_validate_delegates_to_subconfigs(self):
        """Test validate calls subconfig validation."""
        config = PipelineConfig()
        config.github_archive.connect_timeout = -1.0

        with self.assertRaises(ValueError):
            config.validate()


if __name__ == "__main__":
    unittest.main()

