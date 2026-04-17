"""
Storage abstraction layer for uploading files.

Design Pattern: Strategy Pattern
Provides unified interface for different storage backends (GCS, MinIO/S3).
"""
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    def upload_file(
        self,
        local_path: Path,
        remote_path: str,
        content_type: Optional[str] = None,
    ) -> str:
        """
        Upload a file to storage.

        Args:
            local_path: Path to local file
            remote_path: Remote path/key in storage
            content_type: Content type (MIME type)

        Returns:
            URL or path to uploaded file

        Raises:
            StorageError: If upload fails
        """
        pass

    @abstractmethod
    def download_file(self, remote_path: str, local_path: Path) -> None:
        """Download a file from storage."""
        pass

    @abstractmethod
    def file_exists(self, remote_path: str) -> bool:
        """Check if file exists in storage."""
        pass

    @abstractmethod
    def delete_file(self, remote_path: str) -> None:
        """Delete a file from storage."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Clean up resources."""
        pass

    def __enter__(self) -> "StorageBackend":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


class StorageError(Exception):
    """Base exception for storage operations."""
    pass


class GCSBackend(StorageBackend):
    """Google Cloud Storage backend."""

    def __init__(self, bucket_name: str, project_id: Optional[str] = None):
        """
        Initialize GCS backend.

        Args:
            bucket_name: GCS bucket name
            project_id: GCP project ID (optional, uses default credentials)
        """
        try:
            from google.cloud import storage
        except ImportError:
            raise ImportError(
                "google-cloud-storage is required for GCS. "
                "Install with: pip install google-cloud-storage"
            )

        self.bucket_name = bucket_name
        self.project_id = project_id
        self.client = storage.Client(project=project_id)
        self.bucket = self.client.bucket(bucket_name)

        logger.info(
            "Initialized GCS backend",
            extra={"bucket": bucket_name, "project": project_id},
        )

    def upload_file(
        self,
        local_path: Path,
        remote_path: str,
        content_type: Optional[str] = None,
    ) -> str:
        """Upload file to GCS."""
        if not local_path.exists():
            raise StorageError(f"Local file not found: {local_path}")

        try:
            blob = self.bucket.blob(remote_path)

            # Set content type if provided
            if content_type:
                blob.content_type = content_type

            blob.upload_from_filename(str(local_path))

            gs_url = f"gs://{self.bucket_name}/{remote_path}"
            logger.info(
                "Uploaded file to GCS",
                extra={
                    "local_path": str(local_path),
                    "remote_path": remote_path,
                    "size_bytes": local_path.stat().st_size,
                },
            )
            return gs_url

        except Exception as e:
            logger.exception("Failed to upload to GCS", extra={"error": str(e)})
            raise StorageError(f"Failed to upload to GCS: {e}") from e

    def download_file(self, remote_path: str, local_path: Path) -> None:
        """Download file from GCS."""
        try:
            blob = self.bucket.blob(remote_path)
            local_path.parent.mkdir(parents=True, exist_ok=True)
            blob.download_to_filename(str(local_path))

            logger.info(
                "Downloaded file from GCS",
                extra={"remote_path": remote_path, "local_path": str(local_path)},
            )

        except Exception as e:
            logger.exception("Failed to download from GCS", extra={"error": str(e)})
            raise StorageError(f"Failed to download from GCS: {e}") from e

    def file_exists(self, remote_path: str) -> bool:
        """Check if file exists in GCS."""
        blob = self.bucket.blob(remote_path)
        return blob.exists()

    def delete_file(self, remote_path: str) -> None:
        """Delete file from GCS."""
        try:
            blob = self.bucket.blob(remote_path)
            blob.delete()
            logger.info("Deleted file from GCS", extra={"remote_path": remote_path})

        except Exception as e:
            logger.exception("Failed to delete from GCS", extra={"error": str(e)})
            raise StorageError(f"Failed to delete from GCS: {e}") from e

    def close(self) -> None:
        """Close GCS client."""
        if hasattr(self, "client"):
            self.client.close()


class MinIOBackend(StorageBackend):
    """MinIO/S3-compatible storage backend for local development."""

    def __init__(
        self,
        endpoint: str,
        bucket_name: str,
        access_key: str,
        secret_key: str,
        secure: bool = False,
    ):
        """
        Initialize MinIO backend.

        Args:
            endpoint: MinIO endpoint (e.g., 'localhost:9000')
            bucket_name: Bucket name
            access_key: Access key
            secret_key: Secret key
            secure: Use HTTPS if True
        """
        try:
            from minio import Minio
        except ImportError:
            raise ImportError(
                "minio is required for MinIO support. "
                "Install with: pip install minio"
            )

        self.endpoint = endpoint
        self.bucket_name = bucket_name
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )

        # Create bucket if it doesn't exist
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)
            logger.info(f"Created bucket: {bucket_name}")

        logger.info(
            "Initialized MinIO backend",
            extra={"endpoint": endpoint, "bucket": bucket_name},
        )

    def upload_file(
        self,
        local_path: Path,
        remote_path: str,
        content_type: Optional[str] = None,
    ) -> str:
        """Upload file to MinIO."""
        if not local_path.exists():
            raise StorageError(f"Local file not found: {local_path}")

        try:
            file_size = local_path.stat().st_size

            self.client.fput_object(
                self.bucket_name,
                remote_path,
                str(local_path),
                content_type=content_type or "application/octet-stream",
            )

            url = f"s3://{self.bucket_name}/{remote_path}"
            logger.info(
                "Uploaded file to MinIO",
                extra={
                    "local_path": str(local_path),
                    "remote_path": remote_path,
                    "size_bytes": file_size,
                },
            )
            return url

        except Exception as e:
            logger.exception("Failed to upload to MinIO", extra={"error": str(e)})
            raise StorageError(f"Failed to upload to MinIO: {e}") from e

    def download_file(self, remote_path: str, local_path: Path) -> None:
        """Download file from MinIO."""
        try:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            self.client.fget_object(
                self.bucket_name,
                remote_path,
                str(local_path),
            )

            logger.info(
                "Downloaded file from MinIO",
                extra={"remote_path": remote_path, "local_path": str(local_path)},
            )

        except Exception as e:
            logger.exception("Failed to download from MinIO", extra={"error": str(e)})
            raise StorageError(f"Failed to download from MinIO: {e}") from e

    def file_exists(self, remote_path: str) -> bool:
        """Check if file exists in MinIO."""
        try:
            self.client.stat_object(self.bucket_name, remote_path)
            return True
        except Exception:
            return False

    def delete_file(self, remote_path: str) -> None:
        """Delete file from MinIO."""
        try:
            self.client.remove_object(self.bucket_name, remote_path)
            logger.info("Deleted file from MinIO", extra={"remote_path": remote_path})

        except Exception as e:
            logger.exception("Failed to delete from MinIO", extra={"error": str(e)})
            raise StorageError(f"Failed to delete from MinIO: {e}") from e

    def close(self) -> None:
        """Close MinIO client (no-op for MinIO)."""
        pass

