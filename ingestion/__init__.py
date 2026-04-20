"""
GitHub Archive Data Pipeline - Ingestion Package

This package provides components for downloading, storing, and ingesting
GitHub Archive data into databases.

Core Components:
    - GitHubArchiveClient: HTTP client for downloading GitHub Archive data
    - StorageBackend: Storage abstraction (MinIO/GCS)
    - DatabaseBackend: Database abstraction (PostgreSQL/BigQuery)
    - Factories: Factory classes for creating configured instances
    - Logging: Centralized logging configuration

Quick Start:
    from ingestion import setup_logging, get_logger
    from ingestion.factory import GitHubArchiveClientFactory
    from ingestion.backends import StorageFactory, DatabaseFactory

    # Setup logging
    setup_logging()
    logger = get_logger(__name__)

    # Create clients
    client = GitHubArchiveClientFactory.create_for_production()
    storage = StorageFactory.create_local()
    database = DatabaseFactory.create_local()
"""

# Import logging utilities for convenient access
from ingestion.logging_config import (
    setup_logging,
    get_logger,
    configure_for_production,
    configure_for_development,
)

# Import main client
from ingestion.github_archive_client import (
    GitHubArchiveClient,
    GitHubArchiveClientError,
    GitHubArchiveDownloadError,
)

# Import config
from ingestion.config import (
    PipelineConfig,
    GitHubArchiveConfig,
    DownloadConfig,
    LoggingConfig,
    StorageConfig,
    DatabaseConfig,
)

__all__ = [
    # Logging
    "setup_logging",
    "get_logger",
    "configure_for_production",
    "configure_for_development",
    # Client
    "GitHubArchiveClient",
    "GitHubArchiveClientError",
    "GitHubArchiveDownloadError",
    # Config
    "PipelineConfig",
    "GitHubArchiveConfig",
    "DownloadConfig",
    "LoggingConfig",
    "StorageConfig",
    "DatabaseConfig",
]

