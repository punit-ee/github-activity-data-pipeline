"""
Configuration management for GitHub Archive data pipeline.

Design Pattern: Configuration Object Pattern
Provides centralized, type-safe configuration management.
"""
import os
from dataclasses import dataclass, field
from typing import Tuple, Optional


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
class StorageConfig:
    """Configuration for storage backends."""

    # Storage type: 'gcs' or 'minio'
    backend: str = "minio"

    # GCS settings
    gcs_bucket: str = "github-archive-data"
    gcs_project_id: Optional[str] = None

    # MinIO settings
    minio_endpoint: str = "localhost:9000"
    minio_bucket: str = "github-archive"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False

    @classmethod
    def from_env(cls) -> "StorageConfig":
        """Create configuration from environment variables."""
        return cls(
            backend=os.getenv("STORAGE_BACKEND", "minio"),
            gcs_bucket=os.getenv("GCS_BUCKET", "github-archive-data"),
            gcs_project_id=os.getenv("GCS_PROJECT_ID"),
            minio_endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
            minio_bucket=os.getenv("MINIO_BUCKET", "github-archive"),
            minio_access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            minio_secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            minio_secure=os.getenv("MINIO_SECURE", "false").lower() == "true",
        )

    def validate(self) -> None:
        """Validate storage configuration."""
        if self.backend not in ("gcs", "minio"):
            raise ValueError("backend must be 'gcs' or 'minio'")

        if self.backend == "gcs" and not self.gcs_bucket:
            raise ValueError("gcs_bucket is required for GCS backend")

        if self.backend == "minio":
            if not self.minio_endpoint:
                raise ValueError("minio_endpoint is required for MinIO backend")
            if not self.minio_bucket:
                raise ValueError("minio_bucket is required for MinIO backend")


@dataclass
class DatabaseConfig:
    """Configuration for database backends."""

    # Database type: 'postgresql' or 'bigquery'
    backend: str = "postgresql"

    # PostgreSQL settings
    pg_host: str = "localhost"
    pg_port: int = 5432
    pg_database: str = "github_archive"
    pg_user: str = "postgres"
    pg_password: str = "postgres"
    pg_schema: str = "public"
    pg_use_pooling: bool = False  # Enable for parallel Airflow tasks
    pg_pool_size: int = 10  # Max connections in pool

    # BigQuery settings
    bq_project_id: Optional[str] = None
    bq_dataset_id: str = "github_archive"
    bq_location: str = "US"

    # Common settings
    batch_size: int = 5000

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Create configuration from environment variables."""
        return cls(
            backend=os.getenv("DATABASE_BACKEND", "postgresql"),
            pg_host=os.getenv("POSTGRES_HOST", "localhost"),
            pg_port=int(os.getenv("POSTGRES_PORT", "5432")),
            pg_database=os.getenv("POSTGRES_DATABASE", "github_archive"),
            pg_user=os.getenv("POSTGRES_USER", "postgres"),
            pg_password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            pg_schema=os.getenv("POSTGRES_SCHEMA", "public"),
            pg_use_pooling=os.getenv("POSTGRES_USE_POOLING", "false").lower() == "true",
            pg_pool_size=int(os.getenv("POSTGRES_POOL_SIZE", "10")),
            bq_project_id=os.getenv("BIGQUERY_PROJECT_ID"),
            bq_dataset_id=os.getenv("BIGQUERY_DATASET", "github_archive"),
            bq_location=os.getenv("BIGQUERY_LOCATION", "US"),
            batch_size=int(os.getenv("DATABASE_BATCH_SIZE", "1000")),
        )

    def validate(self) -> None:
        """Validate database configuration."""
        if self.backend not in ("postgresql", "bigquery"):
            raise ValueError("backend must be 'postgresql' or 'bigquery'")

        if self.backend == "postgresql":
            if not self.pg_host:
                raise ValueError("pg_host is required for PostgreSQL backend")
            if self.pg_port <= 0:
                raise ValueError("pg_port must be positive")

        if self.backend == "bigquery" and not self.bq_project_id:
            raise ValueError("bq_project_id is required for BigQuery backend")

        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")


@dataclass
class PipelineConfig:
    """Master configuration combining all sub-configs."""

    github_archive: GitHubArchiveConfig = field(default_factory=GitHubArchiveConfig)
    download: DownloadConfig = field(default_factory=DownloadConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)

    @classmethod
    def from_env(cls) -> "PipelineConfig":
        """Create complete pipeline configuration from environment."""
        return cls(
            github_archive=GitHubArchiveConfig.from_env(),
            download=DownloadConfig.from_env(),
            logging=LoggingConfig.from_env(),
            storage=StorageConfig.from_env(),
            database=DatabaseConfig.from_env(),
        )

    def validate(self) -> None:
        """Validate all configuration sections."""
        self.github_archive.validate()
        self.storage.validate()
        self.database.validate()

