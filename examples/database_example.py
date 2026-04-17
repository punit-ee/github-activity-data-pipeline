"""
Simple example: Ingest data to database (PostgreSQL for local, BigQuery for production).

This demonstrates the database abstraction layer with best practices.
"""
import gzip
import json
import logging
from pathlib import Path

from ingestion.backends import DatabaseFactory
from ingestion.config import DatabaseConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def ingest_to_local_database():
    """Ingest data to PostgreSQL (local development)."""
    logger.info("=== Ingesting to PostgreSQL (Local) ===")

    # Create PostgreSQL backend
    database = DatabaseFactory.create_local()

    # Create a test file with sample GitHub events
    test_file = Path("./test_data/sample_events.json.gz")
    test_file.parent.mkdir(exist_ok=True)

    # Generate sample events
    sample_events = [
        {
            "id": "12345",
            "type": "PushEvent",
            "actor": {"login": "testuser", "id": 1},
            "repo": {"name": "test/repo", "id": 1},
            "payload": {"commits": []},
            "public": True,
            "created_at": "2026-04-16T10:00:00Z",
        },
        {
            "id": "12346",
            "type": "IssuesEvent",
            "actor": {"login": "testuser2", "id": 2},
            "repo": {"name": "test/repo2", "id": 2},
            "payload": {"action": "opened"},
            "public": True,
            "created_at": "2026-04-16T10:01:00Z",
        },
    ]

    with gzip.open(test_file, "wt", encoding="utf-8") as f:
        for event in sample_events:
            f.write(json.dumps(event) + "\n")

    try:
        with database:
            # Ingest data
            metrics = database.ingest_from_file(
                file_path=test_file,
                table_name="github_events",
                batch_size=100,
            )

            if metrics.success:
                logger.info(
                    f"✅ Ingested {metrics.rows_inserted} rows "
                    f"in {metrics.duration_seconds:.2f}s"
                )

                # Query the data
                results = database.execute_query(
                    "SELECT type, COUNT(*) as count "
                    "FROM public.github_events "
                    "GROUP BY type"
                )
                logger.info(f"Event counts: {results}")

            else:
                logger.error(f"❌ Ingestion failed: {metrics.error_message}")

    except Exception as e:
        logger.exception(f"Database operation failed: {e}")


def ingest_to_production_database():
    """Ingest data to BigQuery (production)."""
    logger.info("=== Ingesting to BigQuery (Production) ===")

    # Create BigQuery backend
    config = DatabaseConfig(
        backend="bigquery",
        bq_project_id="your-project-id",
        bq_dataset_id="github_archive",
    )

    database = DatabaseFactory.create_from_config(config)

    # Use the same test file
    test_file = Path("./test_data/sample_events.json.gz")

    if not test_file.exists():
        logger.error("Test file not found. Run local example first.")
        return

    try:
        with database:
            # Ingest data
            metrics = database.ingest_from_file(
                file_path=test_file,
                table_name="github_events",
                batch_size=1000,
            )

            if metrics.success:
                logger.info(
                    f"✅ Ingested {metrics.rows_inserted} rows "
                    f"in {metrics.duration_seconds:.2f}s"
                )

                # Query the data
                results = database.execute_query(
                    "SELECT type, COUNT(*) as count "
                    "FROM github_archive.github_events "
                    "GROUP BY type"
                )
                logger.info(f"Event counts: {results}")

            else:
                logger.error(f"❌ Ingestion failed: {metrics.error_message}")

    except Exception as e:
        logger.exception(f"Database operation failed: {e}")


if __name__ == "__main__":
    import os

    mode = os.getenv("MODE", "local")

    if mode == "local":
        ingest_to_local_database()
    else:
        ingest_to_production_database()

