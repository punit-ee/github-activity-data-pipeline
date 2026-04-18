"""
Factory classes for storage and database backends.

Design Pattern: Factory Pattern + Strategy Pattern
Creates appropriate backend instances based on configuration.
"""
from typing import Union

from ingestion.config import StorageConfig, DatabaseConfig
from ingestion.storage import StorageBackend, GCSBackend, MinIOBackend
from ingestion.database import DatabaseBackend, PostgreSQLBackend, BigQueryBackend


class StorageFactory:
    """Factory for creating storage backend instances."""

    @staticmethod
    def create_from_config(config: StorageConfig) -> StorageBackend:
        """
        Create storage backend from configuration.

        Args:
            config: StorageConfig instance

        Returns:
            Configured StorageBackend

        Raises:
            ValueError: If backend type is invalid
        """
        config.validate()

        if config.backend == "gcs":
            return GCSBackend(
                bucket_name=config.gcs_bucket,
                project_id=config.gcs_project_id,
            )
        elif config.backend == "minio":
            return MinIOBackend(
                endpoint=config.minio_endpoint,
                bucket_name=config.minio_bucket,
                access_key=config.minio_access_key,
                secret_key=config.minio_secret_key,
                secure=config.minio_secure,
            )
        else:
            raise ValueError(f"Unknown storage backend: {config.backend}")

    @staticmethod
    def create_local() -> StorageBackend:
        """Create MinIO backend for local development."""
        config = StorageConfig(backend="minio")
        return StorageFactory.create_from_config(config)

    @staticmethod
    def create_production(
        bucket_name: str,
        project_id: str = None,
    ) -> StorageBackend:
        """Create GCS backend for production."""
        config = StorageConfig(
            backend="gcs",
            gcs_bucket=bucket_name,
            gcs_project_id=project_id,
        )
        return StorageFactory.create_from_config(config)


class DatabaseFactory:
    """Factory for creating database backend instances."""

    @staticmethod
    def create_from_config(config: DatabaseConfig) -> DatabaseBackend:
        """
        Create database backend from configuration.

        Args:
            config: DatabaseConfig instance

        Returns:
            Configured DatabaseBackend

        Raises:
            ValueError: If backend type is invalid
        """
        config.validate()

        if config.backend == "postgresql":
            return PostgreSQLBackend(
                host=config.pg_host,
                port=config.pg_port,
                database=config.pg_database,
                user=config.pg_user,
                password=config.pg_password,
                schema=config.pg_schema,
                use_pooling=config.pg_use_pooling,
                pool_size=config.pg_pool_size,
            )
        elif config.backend == "bigquery":
            return BigQueryBackend(
                project_id=config.bq_project_id,
                dataset_id=config.bq_dataset_id,
                location=config.bq_location,
            )
        else:
            raise ValueError(f"Unknown database backend: {config.backend}")

    @staticmethod
    def create_local(
        database: str = "github_archive",
        user: str = "postgres",
        password: str = "postgres",
    ) -> DatabaseBackend:
        """Create PostgreSQL backend for local development."""
        config = DatabaseConfig(
            backend="postgresql",
            pg_database=database,
            pg_user=user,
            pg_password=password,
        )
        return DatabaseFactory.create_from_config(config)

    @staticmethod
    def create_production(
        project_id: str,
        dataset_id: str = "github_archive",
    ) -> DatabaseBackend:
        """Create BigQuery backend for production."""
        config = DatabaseConfig(
            backend="bigquery",
            bq_project_id=project_id,
            bq_dataset_id=dataset_id,
        )
        return DatabaseFactory.create_from_config(config)

