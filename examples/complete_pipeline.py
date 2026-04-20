"""
Complete pipeline example: Download -> Upload to Storage -> Ingest to Database

This example demonstrates the full pipeline:
- Download GitHub Archive data
- Upload to storage (MinIO/GCS)
- Ingest into raw.github_events table (PostgreSQL/BigQuery)
- Configurable for local/production

Database backends:
- PostgreSQL: RawTableLoader with staging table pattern (15K+ rows/sec)
- BigQuery: RawTableLoader with MERGE pattern (28K+ rows/sec)
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ingestion import setup_logging, get_logger
from ingestion.factory import GitHubArchiveClientFactory
from ingestion.backends import StorageFactory, DatabaseFactory
from ingestion.config import PipelineConfig
from ingestion.github_archive_client import GitHubArchiveDownloadError

# Setup centralized logging
setup_logging()
logger = get_logger(__name__)


def run_pipeline_for_hour(
    date_hour: str,
    local_dir: Path,
    storage_backend,
    database_backend,
) -> bool:
    """
    Run complete pipeline for a single hour.

    Args:
        date_hour: Hour to process (YYYY-MM-DD-HH)
        local_dir: Local directory for temporary files
        storage_backend: Storage backend instance
        database_backend: Database backend instance

    Returns:
        True if successful, False otherwise
    """
    local_dir.mkdir(parents=True, exist_ok=True)
    local_file = local_dir / f"{date_hour}.json.gz"

    try:
        # Step 1: Download from GitHub Archive
        logger.info(f"[{date_hour}] Step 1/3: Downloading from GitHub Archive")

        with GitHubArchiveClientFactory.create_default() as client:
            response = client.download_events(date_hour)

            with open(local_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)

        file_size_mb = local_file.stat().st_size / (1024 * 1024)
        logger.info(f"[{date_hour}] Downloaded {file_size_mb:.2f} MB")

        # Step 2: Upload to storage
        logger.info(f"[{date_hour}] Step 2/3: Uploading to storage")

        remote_path = f"github-archive/{date_hour}.json.gz"
        storage_url = storage_backend.upload_file(
            local_path=local_file,
            remote_path=remote_path,
            content_type="application/gzip",
        )
        logger.info(f"[{date_hour}] Uploaded to: {storage_url}")

        # Step 3: Ingest into raw.github_events table
        logger.info(f"[{date_hour}] Step 3/3: Ingesting into raw.github_events table")

        metrics = database_backend.ingest_from_file(
            file_path=local_file,
            table_name="github_events",
        )

        if not metrics.success:
            logger.error(f"[{date_hour}] Ingestion failed: {metrics.error_message}")
            return False

        logger.info(
            f"[{date_hour}] Ingested {metrics.rows_inserted:,} rows "
            f"in {metrics.duration_seconds:.2f}s "
            f"({metrics.rows_inserted/metrics.duration_seconds:.0f} rows/sec)"
        )

        # Cleanup local file
        local_file.unlink()
        logger.info(f"[{date_hour}] ✅ Pipeline completed successfully")
        return True

    except GitHubArchiveDownloadError as e:
        logger.error(f"[{date_hour}] Download failed: {e}")
        return False
    except Exception as e:
        logger.exception(f"[{date_hour}] Pipeline failed: {e}")
        return False


def main_local():
    """Run pipeline in local mode (MinIO + PostgreSQL)."""
    logger.info("=== Running Pipeline in LOCAL mode ===")
    logger.info("Using: MinIO (storage) + PostgreSQL (database)")

    # Load configuration
    config = PipelineConfig.from_env()

    # Override for local
    config.storage.backend = "minio"
    config.database.backend = "postgresql"
    config.validate()

    # Create backends
    storage = StorageFactory.create_from_config(config.storage)
    database = DatabaseFactory.create_from_config(config.database)

    # Process recent hour (current time - 2 hours)
    current = datetime.now(timezone.utc) - timedelta(hours=2)
    date_hour = f"{current.year}-{current.month:02d}-{current.day:02d}-{current.hour}"
    local_dir = Path("./data/pipeline")

    try:
        with storage, database:
            success = run_pipeline_for_hour(
                date_hour=date_hour,
                local_dir=local_dir,
                storage_backend=storage,
                database_backend=database,
            )

        return 0 if success else 1

    except Exception as e:
        logger.exception(f"Pipeline failed: {e}")
        return 1


def main_production():
    """Run pipeline in production mode (GCS + BigQuery)."""
    logger.info("=== Running Pipeline in PRODUCTION mode ===")
    logger.info("Using: GCS (storage) + BigQuery (database)")

    # Load configuration from environment
    config = PipelineConfig.from_env()

    # Override for production
    config.storage.backend = "gcs"
    config.database.backend = "bigquery"
    config.validate()

    # Create backends
    storage = StorageFactory.create_from_config(config.storage)
    database = DatabaseFactory.create_from_config(config.database)

    # Process recent hour (current time - 2 hours)
    date_hour = (datetime.now(timezone.utc) - timedelta(hours=2)).strftime("%Y-%m-%d-%H")
    local_dir = Path("/tmp/github-archive")

    try:
        with storage, database:
            success = run_pipeline_for_hour(
                date_hour=date_hour,
                local_dir=local_dir,
                storage_backend=storage,
                database_backend=database,
            )

        return 0 if success else 1

    except Exception as e:
        logger.exception(f"Pipeline failed: {e}")
        return 1


def main_batch():
    """Run pipeline for multiple hours."""
    logger.info("=== Running BATCH Pipeline ===")

    # Load configuration
    config = PipelineConfig.from_env()
    config.validate()

    logger.info(f"Storage: {config.storage.backend}")
    logger.info(f"Database: {config.database.backend}")

    # Create backends
    storage = StorageFactory.create_from_config(config.storage)
    database = DatabaseFactory.create_from_config(config.database)

    # Process last 24 hours
    start_time = datetime.now(timezone.utc) - timedelta(hours=24)
    local_dir = Path("./data/batch")

    results = {"success": 0, "failed": 0}

    try:
        with storage, database:
            for hour_offset in range(24):
                dt = start_time + timedelta(hours=hour_offset)
                date_hour = dt.strftime("%Y-%m-%d-%H")

                success = run_pipeline_for_hour(
                    date_hour=date_hour,
                    local_dir=local_dir,
                    storage_backend=storage,
                    database_backend=database,
                )

                if success:
                    results["success"] += 1
                else:
                    results["failed"] += 1

        logger.info(f"Batch pipeline completed: {results}")
        return 0 if results["failed"] == 0 else 1

    except Exception as e:
        logger.exception(f"Batch pipeline failed: {e}")
        return 1


if __name__ == "__main__":
    import os

    mode = os.getenv("PIPELINE_MODE", "local")

    if mode == "local":
        sys.exit(main_local())
    elif mode == "production":
        sys.exit(main_production())
    elif mode == "batch":
        sys.exit(main_batch())
    else:
        logger.error(f"Unknown mode: {mode}. Use 'local', 'production', or 'batch'")
        sys.exit(1)

