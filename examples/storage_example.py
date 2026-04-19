"""
Simple example: Upload file to storage (MinIO for local, GCS for production).

This demonstrates the storage abstraction layer.
"""
import logging
from pathlib import Path

from ingestion.backends import StorageFactory
from ingestion.config import StorageConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def upload_to_local_storage():
    """Upload file to MinIO (local development)."""
    logger.info("=== Uploading to MinIO (Local) ===")

    # Create MinIO backend
    storage = StorageFactory.create_local()

    # Create a test file
    test_file = Path("./test_data/sample.json.gz")
    test_file.parent.mkdir(exist_ok=True)
    test_file.write_text('{"test": "data"}\n')

    try:
        with storage:
            # Upload file
            remote_path = "test/sample.json.gz"
            url = storage.upload_file(
                local_path=test_file,
                remote_path=remote_path,
                content_type="application/gzip",
            )

            logger.info(f"✅ Uploaded to: {url}")

            # Check if file exists
            exists = storage.file_exists(remote_path)
            logger.info(f"File exists: {exists}")

            # Download it back
            download_path = Path("./test_data/downloaded.json.gz")
            storage.download_file(remote_path, download_path)
            logger.info(f"✅ Downloaded to: {download_path}")

    except Exception as e:
        logger.exception(f"Upload failed: {e}")


def upload_to_production_storage():
    """Upload file to GCS (production)."""
    logger.info("=== Uploading to GCS (Production) ===")

    # Create GCS backend
    config = StorageConfig(
        backend="gcs",
        gcs_bucket="your-bucket-name",
        gcs_project_id="your-project-id",
    )

    storage = StorageFactory.create_from_config(config)

    # Create a test file
    test_file = Path("./test_data/sample.json.gz")
    test_file.parent.mkdir(exist_ok=True)
    test_file.write_text('{"test": "data"}\n')

    try:
        with storage:
            # Upload file
            remote_path = "test/sample.json.gz"
            url = storage.upload_file(
                local_path=test_file,
                remote_path=remote_path,
                content_type="application/gzip",
            )

            logger.info(f"✅ Uploaded to: {url}")

    except Exception as e:
        logger.exception(f"Upload failed: {e}")


if __name__ == "__main__":
    import os

    mode = os.getenv("MODE", "local")

    if mode == "local":
        upload_to_local_storage()
    else:
        upload_to_production_storage()

