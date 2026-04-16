"""
Configuration management for GitHub Archive data pipeline.

Design Pattern: Configuration Object Pattern
Provides centralized, type-safe configuration management.
"""
import os
from dataclasses import dataclass, field
from typing import Tuple


@dataclass
class GitHubArchiveConfig:
    """Configuration for GitHubArchiveClient."""

    # Network settings
    connect_timeout: float = 5.0
    read_timeout: float = 30.0

    # Retry settings
    max_retries: int = 3
    retry_backoff_factor: float = 0.5
    retry_status_codes: Tuple[int, ...] = (429, 500, 502, 503, 504)

    # User agent
    user_agent: str = "github-activity-data-pipeline/1.0"

    # Base URL (can be overridden for testing)
    base_url: str = "https://data.gharchive.org"

    @property
    def timeout(self) -> Tuple[float, float]:
        """Get timeout as (connect, read) tuple."""
        return (self.connect_timeout, self.read_timeout)

    @classmethod
    def from_env(cls) -> "GitHubArchiveConfig":
        """
        Create configuration from environment variables.

        Environment variables:
        - GITHUB_ARCHIVE_CONNECT_TIMEOUT: Connection timeout in seconds
        - GITHUB_ARCHIVE_READ_TIMEOUT: Read timeout in seconds
        - GITHUB_ARCHIVE_MAX_RETRIES: Maximum retry attempts
        - GITHUB_ARCHIVE_USER_AGENT: Custom user agent string
        - GITHUB_ARCHIVE_BASE_URL: Base URL override
        """
        return cls(
            connect_timeout=float(os.getenv("GITHUB_ARCHIVE_CONNECT_TIMEOUT", "5.0")),
            read_timeout=float(os.getenv("GITHUB_ARCHIVE_READ_TIMEOUT", "30.0")),
            max_retries=int(os.getenv("GITHUB_ARCHIVE_MAX_RETRIES", "3")),
            retry_backoff_factor=float(os.getenv("GITHUB_ARCHIVE_RETRY_BACKOFF", "0.5")),
            user_agent=os.getenv(
                "GITHUB_ARCHIVE_USER_AGENT",
                "github-activity-data-pipeline/1.0",
            ),
            base_url=os.getenv(
                "GITHUB_ARCHIVE_BASE_URL",
                "https://data.gharchive.org",
            ),
        )

    def validate(self) -> None:
        """
        Validate configuration values.

        Raises:
            ValueError: If configuration is invalid
        """
        if self.connect_timeout <= 0:
            raise ValueError("connect_timeout must be positive")

        if self.read_timeout <= 0:
            raise ValueError("read_timeout must be positive")

        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")

        if self.retry_backoff_factor < 0:
            raise ValueError("retry_backoff_factor must be non-negative")

        if not self.base_url:
            raise ValueError("base_url cannot be empty")


@dataclass
class DownloadConfig:
    """Configuration for download operations."""

    # Download settings
    chunk_size: int = 1024 * 1024  # 1MB default
    max_workers: int = 3

    # File settings
    output_dir: str = "./data"
    overwrite_existing: bool = False

    @classmethod
    def from_env(cls) -> "DownloadConfig":
        """Create configuration from environment variables."""
        return cls(
            chunk_size=int(os.getenv("DOWNLOAD_CHUNK_SIZE", str(1024 * 1024))),
            max_workers=int(os.getenv("DOWNLOAD_MAX_WORKERS", "3")),
            output_dir=os.getenv("DOWNLOAD_OUTPUT_DIR", "./data"),
            overwrite_existing=os.getenv("DOWNLOAD_OVERWRITE", "false").lower() == "true",
        )


@dataclass
class LoggingConfig:
    """Configuration for logging."""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    json_format: bool = False

    @classmethod
    def from_env(cls) -> "LoggingConfig":
        """Create configuration from environment variables."""
        return cls(
            level=os.getenv("LOG_LEVEL", "INFO").upper(),
            format=os.getenv(
                "LOG_FORMAT",
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            ),
            json_format=os.getenv("LOG_JSON", "false").lower() == "true",
        )


@dataclass
class PipelineConfig:
    """Master configuration combining all sub-configs."""

    github_archive: GitHubArchiveConfig = field(default_factory=GitHubArchiveConfig)
    download: DownloadConfig = field(default_factory=DownloadConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    @classmethod
    def from_env(cls) -> "PipelineConfig":
        """Create complete pipeline configuration from environment."""
        return cls(
            github_archive=GitHubArchiveConfig.from_env(),
            download=DownloadConfig.from_env(),
            logging=LoggingConfig.from_env(),
        )

    def validate(self) -> None:
        """Validate all configuration sections."""
        self.github_archive.validate()

