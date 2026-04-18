"""
GitHub Archive Data Pipeline - Airflow DAG (Enhanced)

Production-ready DAG with SEPARATE TASKS for better visibility:
- Task 1: Download from GitHub Archive
- Task 2: Upload to Storage (MinIO/GCS)
- Task 3: Ingest to Database (PostgreSQL/BigQuery)

Benefits of separate tasks:
- Better visibility in Airflow UI
- Individual task retries
- Easier debugging
- Clear task duration metrics
- Proper XCom data passing

Design Pattern: Incremental ETL with State Management
Built with: @dag and @task decorators
"""
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any

from airflow.decorators import dag, task
from airflow.models import Variable
from airflow.exceptions import AirflowSkipException

# Import pipeline components
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.factory import GitHubArchiveClientFactory
from ingestion.backends import StorageFactory, DatabaseFactory
from ingestion.config import PipelineConfig
from ingestion.github_archive_client import GitHubArchiveDownloadError


logger = logging.getLogger(__name__)


# Airflow Variable keys for manual backfill mode
BACKFILL_START_KEY = "github_archive_backfill_start"
BACKFILL_END_KEY = "github_archive_backfill_end"


def get_last_processed_hour_from_db() -> Optional[datetime]:
    """
    Query raw.github_events table to find the most recent source_file processed.
    
    Returns:
        Datetime of the last processed hour, or None if table is empty.
    """
    try:
        config = PipelineConfig.from_env()
        database = DatabaseFactory.create_from_config(config.database)

        with database:
            last_hour = database.get_last_processed_hour()

        return last_hour

    except Exception as e:
        logger.warning(f"Could not query last processed hour from DB: {e}")
        return None


def get_backfill_range() -> Optional[tuple]:
    """Get backfill range if manual backfill is requested."""
    try:
        start_str = Variable.get(BACKFILL_START_KEY, default_var=None)
        end_str = Variable.get(BACKFILL_END_KEY, default_var=None)
        if start_str and end_str:
            start_dt = datetime.strptime(start_str, "%Y-%m-%d-%H")
            end_dt = datetime.strptime(end_str, "%Y-%m-%d-%H")
            return (start_dt, end_dt)
    except Exception:
        pass
    return None


def clear_backfill_range() -> None:
    """Clear backfill variables after completion."""
    try:
        Variable.delete(BACKFILL_START_KEY)
        Variable.delete(BACKFILL_END_KEY)
    except Exception:
        pass


@dag(
    dag_id='github_archive_pipeline',
    description='Hourly ingestion with separate Download → Upload → Ingest tasks',
    schedule='0 * * * *',  # Runs every hour at minute 0 UTC
    start_date=datetime(2026, 4, 18),
    catchup=False,
    max_active_runs=1,
    max_active_tasks=4,  # Limit to 4 parallel tasks to prevent OOM
    default_args={
        'owner': 'data-team',
        'depends_on_past': False,
        'email': ['data-team@example.com'],
        'email_on_failure': True,
        'email_on_retry': False,
        'retries': 3,
        'retry_delay': timedelta(minutes=5),
        'execution_timeout': timedelta(hours=2),
        'max_active_tis_per_dag': 4,  # Max 4 task instances across all DAG runs
        'max_active_tis_per_dagrun': 4,  # Max 4 task instances per this DAG run
    },
    tags=['github-archive', 'data-ingestion', 'production'],
    doc_md=__doc__,
)
def github_archive_pipeline():
    """
    GitHub Archive ETL Pipeline with separate tasks for each step.

    Pipeline Flow:
    1. Validate configuration
    2. Check data availability
    3. Generate hours to process
    4. For each hour:
       a. Download from GitHub Archive
       b. Upload to Storage (MinIO/GCS)
       c. Ingest to Database (PostgreSQL/BigQuery)
    """

    @task()
    def validate_configuration() -> Dict[str, Any]:
        """Step 1: Validate pipeline configuration."""
        logger.info("🔍 Validating configuration...")

        config = PipelineConfig.from_env()

        try:
            config.validate()
            logger.info("✅ Configuration valid")

            config_info = {
                "storage": config.storage.backend,
                "database": config.database.backend,
                "mode": os.getenv('PIPELINE_MODE', 'not set'),
                "valid": True,
            }

            logger.info("   Storage: %s", config_info["storage"])
            logger.info("   Database: %s", config_info["database"])
            logger.info("   Mode: %s", config_info["mode"])

            return config_info

        except ValueError as e:
            logger.exception("❌ Invalid configuration: %s", e)
            raise

    @task()
    def check_data_availability() -> bool:
        """Step 2: Check if new data is available for processing."""
        current_time = datetime.utcnow()

        if get_backfill_range():
            logger.info("✅ Backfill mode - data will be processed")
        else:
            target_hour = (current_time - timedelta(hours=2)).replace(minute=0, second=0, microsecond=0)
            logger.info("✅ Hourly mode - latest eligible hour: %s", target_hour)

        return True

    @task()
    def generate_hours_to_process() -> List[str]:
        """
        Step 3: Generate list of hours to process.

        Logic:
        - Query raw.github_events for last processed source_file
        - If found: start from last_hour + 1
        - If empty: start from today midnight (00:00)
        - Always end at: current_time - 2 hours
        """
        backfill_range = get_backfill_range()

        if backfill_range:
            # Manual backfill mode
            start_dt, end_dt = backfill_range
            logger.info("📅 Backfill mode: %s to %s", start_dt, end_dt)
        else:
            # Incremental mode - query database
            current_time = datetime.utcnow()
            end_dt = (current_time - timedelta(hours=2)).replace(minute=0, second=0, microsecond=0)

            # Query database for last processed hour
            last_processed = get_last_processed_hour_from_db()

            if last_processed:
                # Start from next hour after last processed
                start_dt = last_processed + timedelta(hours=1)
                logger.info("📅 Incremental mode: Last processed %s, starting from %s",
                           last_processed.strftime("%Y-%m-%d-%H"), start_dt.strftime("%Y-%m-%d-%H"))
            else:
                # No data in table, start from today midnight
                today = current_time.date()
                start_dt = datetime.combine(today, datetime.min.time())
                logger.info("📅 Initial load: Table empty, starting from today midnight %s",
                           start_dt.strftime("%Y-%m-%d-%H"))

            logger.info("📅 Processing until: %s (current - 2 hours)", end_dt.strftime("%Y-%m-%d-%H"))

        # Check if there's anything to process
        if start_dt > end_dt:
            logger.info("✅ No new data to process (already up to date)")
            raise AirflowSkipException("No hours to process")

        # Generate list of hours
        hours_to_process = []
        current = start_dt

        while current <= end_dt:
            # Format: YYYY-MM-DD-H (single digit hours 0-9, no leading zero)
            date_hour = f"{current.year}-{current.month:02d}-{current.day:02d}-{current.hour}"
            hours_to_process.append(date_hour)
            current += timedelta(hours=1)

        if not hours_to_process:
            logger.info("✅ No new data to process")
            raise AirflowSkipException("No hours to process")

        logger.info("📊 Processing %s hours: %s to %s",
                   len(hours_to_process),
                   hours_to_process[0],
                   hours_to_process[-1])
        return hours_to_process

    @task()
    def download_from_github(date_hour: str) -> Dict[str, Any]:
        """
        TASK 1: Download data from GitHub Archive.

        Args:
            date_hour: Hour to download in format YYYY-MM-DD-HH

        Returns:
            Dictionary with download metrics and file path
        """
        import time

        output_dir = Path(os.getenv("DOWNLOAD_OUTPUT_DIR", "/tmp/github-archive"))
        output_dir.mkdir(parents=True, exist_ok=True)
        local_file = output_dir / f"{date_hour}.json.gz"

        start_time = time.time()

        logger.info("⬇️  [Task 1/3] Downloading %s from GitHub Archive...", date_hour)

        with GitHubArchiveClientFactory.create_for_production() as client:
            response = client.download_events(date_hour)

            with open(local_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)

        file_size_mb = local_file.stat().st_size / (1024 * 1024)
        duration = time.time() - start_time

        result = {
            "date_hour": date_hour,
            "file_path": str(local_file),
            "file_size_mb": round(file_size_mb, 2),
            "duration_seconds": round(duration, 2),
        }

        logger.info("✅ Downloaded %.2f MB in %.2fs", file_size_mb, duration)
        return result

    @task()
    def upload_to_storage(download_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        TASK 2: Upload file to Storage (MinIO/GCS).

        Args:
            download_result: Result from download task

        Returns:
            Dictionary with upload metrics
        """
        import time

        date_hour = download_result["date_hour"]
        local_file = Path(download_result["file_path"])

        if not local_file.exists():
            raise FileNotFoundError(f"Downloaded file not found: {local_file}")

        config = PipelineConfig.from_env()
        storage = StorageFactory.create_from_config(config.storage)

        start_time = time.time()

        logger.info("⬆️  [Task 2/3] Uploading %s to %s...", date_hour, config.storage.backend.upper())

        with storage:
            remote_path = f"github-archive/{date_hour}.json.gz"
            storage_url = storage.upload_file(
                local_path=local_file,
                remote_path=remote_path,
                content_type="application/gzip",
            )

        duration = time.time() - start_time

        result = {
            **download_result,  # Include all download info
            "storage_url": storage_url,
            "upload_duration_seconds": round(duration, 2),
        }

        logger.info("✅ Uploaded to %s in %.2fs", storage_url, duration)
        return result

    @task()
    def ingest_to_database(upload_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        TASK 3: Ingest data to Database (PostgreSQL/BigQuery).

        Args:
            upload_result: Result from upload task

        Returns:
            Dictionary with ingestion metrics
        """
        date_hour = upload_result["date_hour"]
        local_file = Path(upload_result["file_path"])

        if not local_file.exists():
            raise FileNotFoundError(f"File not found for ingestion: {local_file}")

        config = PipelineConfig.from_env()
        database = DatabaseFactory.create_from_config(config.database)

        logger.info("💾 [Task 3/3] Ingesting %s to %s...", date_hour, config.database.backend.upper())

        with database:
            metrics = database.ingest_from_file(
                file_path=local_file,
                table_name="github_events",
                batch_size=config.database.batch_size,
            )

        if not metrics.success:
            raise Exception(f"Ingestion failed: {metrics.error_message}")

        logger.info("✅ Ingested %,d rows in %.2fs", metrics.rows_inserted, metrics.duration_seconds)

        # No need to update state - we query raw.github_events table directly

        # Cleanup local file
        if local_file.exists():
            local_file.unlink()
            logger.info("🗑️  Cleaned up temporary file")

        result = {
            **upload_result,  # Include all previous info
            "rows_inserted": metrics.rows_inserted,
            "rows_failed": metrics.rows_failed,
            "ingest_duration_seconds": round(metrics.duration_seconds, 2),
        }

        return result

    @task()
    def summarize_results(ingest_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Final Task: Summarize all processing results.

        Args:
            ingest_results: List of results from all ingest tasks

        Returns:
            Summary statistics
        """
        if not ingest_results:
            return {"success": True, "hours_processed": 0}

        successful = len([r for r in ingest_results if r.get("rows_inserted", 0) > 0])
        failed = len(ingest_results) - successful
        total_rows = sum(r.get("rows_inserted", 0) for r in ingest_results)
        total_size_mb = sum(r.get("file_size_mb", 0) for r in ingest_results)

        summary = {
            "success": failed == 0,
            "hours_processed": successful,
            "hours_failed": failed,
            "total_rows_inserted": total_rows,
            "total_size_mb": round(total_size_mb, 2),
            "average_rows_per_hour": round(total_rows / successful) if successful > 0 else 0,
        }

        logger.info("📊 Pipeline Summary:")
        logger.info("   ✅ Successful: %s/%s hours", successful, len(ingest_results))
        logger.info("   ❌ Failed: %s/%s hours", failed, len(ingest_results))
        logger.info("   📈 Total rows: %,d", total_rows)
        logger.info("   💾 Total size: %.2f MB", total_size_mb)
        logger.info("   📊 Avg rows/hour: %,d", summary['average_rows_per_hour'])

        # Clear backfill variables if in backfill mode
        if get_backfill_range():
            clear_backfill_range()
            logger.info("🧹 Cleared backfill range variables")

        return summary

    # ========================================
    # DAG Task Flow Definition
    # ========================================

    # Step 1: Validate and prepare
    config = validate_configuration()
    availability = check_data_availability()
    hours = generate_hours_to_process()

    # Step 2: Use dynamic task mapping to process each hour
    # This creates 3 tasks per hour dynamically
    # expand() is the Airflow 2.x way to handle dynamic task generation
    downloaded = download_from_github.expand(date_hour=hours)
    uploaded = upload_to_storage.expand(download_result=downloaded)
    ingested = ingest_to_database.expand(upload_result=uploaded)

    # Step 3: Summarize all results
    summary = summarize_results(ingested)

    # Set dependencies
    config >> availability >> hours >> downloaded >> uploaded >> ingested >> summary


# Instantiate the DAG
dag_instance = github_archive_pipeline()


