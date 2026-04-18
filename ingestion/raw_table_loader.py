"""
Raw Table Loader - Production-ready ingestion for Postgres & BigQuery
Implements the table design from scratch_28.sql
"""

import json
import gzip
from datetime import datetime, timezone
from typing import List, Dict, Any, Protocol
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class RawTableLoader(Protocol):
    """Abstract interface for raw table loading"""

    def upsert_batch(self, events: List[Dict[str, Any]], source_file: str) -> int:
        """Upsert a batch of events. Returns count of rows affected."""
        ...


class PostgresRawLoader:
    """
    PostgreSQL implementation using staging table pattern for bulk upsert
    Optimized for billions of rows
    """

    def __init__(self, conn):
        """
        Args:
            conn: psycopg2 connection with autocommit=False
        """
        self.conn = conn

    def _transform_event(self, event: Dict[str, Any]) -> tuple:
        """Transform GitHub event JSON to table row"""
        created_at = datetime.fromisoformat(
            event['created_at'].replace('Z', '+00:00')
        )

        return (
            event['id'],                                    # event_id
            event['type'],                                  # event_type
            created_at,                                     # created_at
            created_at.date(),                             # event_date
            event.get('actor', {}).get('id'),              # actor_id
            event.get('actor', {}).get('login'),           # actor_login
            str(event.get('repo', {}).get('id')) if event.get('repo', {}).get('id') else None,  # repo_id
            event.get('repo', {}).get('name'),             # repo_name
            event.get('org', {}).get('id'),                # org_id
            event.get('org', {}).get('login'),             # org_login
            event.get('public', True),                     # is_public
            json.dumps(event.get('payload', {})),          # payload (JSON as TEXT)
        )

    def upsert_batch(self, events: List[Dict[str, Any]], source_file: str) -> int:
        """
        Bulk upsert using staging table pattern (fastest for Postgres)

        Pattern:
        1. COPY into unlogged staging table (no WAL = fast)
        2. INSERT...SELECT with ON CONFLICT
        3. Cleanup staging

        Args:
            events: List of parsed GitHub event dicts
            source_file: Source filename for lineage tracking

        Returns:
            Number of rows upserted
        """
        if not events:
            return 0

        cursor = self.conn.cursor()

        try:
            # Step 1: Prepare staging table
            cursor.execute("""
                CREATE TEMP TABLE IF NOT EXISTS github_events_staging (
                    LIKE raw.github_events INCLUDING DEFAULTS EXCLUDING INDEXES
                ) ON COMMIT DROP;
                
                TRUNCATE github_events_staging;
            """)

            # Step 2: Bulk insert into staging using execute_values
            from psycopg2.extras import execute_values

            rows = [
                self._transform_event(event) + (source_file,)
                for event in events
            ]

            execute_values(
                cursor,
                """
                INSERT INTO github_events_staging (
                    event_id, event_type, created_at, event_date,
                    actor_id, actor_login, repo_id, repo_name,
                    org_id, org_login, is_public, payload,
                    source_file
                ) VALUES %s
                """,
                rows,
                page_size=1000
            )

            # Step 3: Merge into main table
            cursor.execute("""
                INSERT INTO raw.github_events
                SELECT 
                    event_id, event_type, created_at, event_date,
                    actor_id, actor_login, repo_id, repo_name,
                    org_id, org_login, is_public, payload,
                    source_file,
                    NOW() as ingested_at,
                    NOW() as updated_at
                FROM github_events_staging
                ON CONFLICT (event_id, event_date) DO UPDATE SET
                    event_type   = EXCLUDED.event_type,
                    actor_id     = EXCLUDED.actor_id,
                    actor_login  = EXCLUDED.actor_login,
                    repo_id      = EXCLUDED.repo_id,
                    repo_name    = EXCLUDED.repo_name,
                    org_id       = EXCLUDED.org_id,
                    org_login    = EXCLUDED.org_login,
                    is_public    = EXCLUDED.is_public,
                    payload      = EXCLUDED.payload,
                    source_file  = EXCLUDED.source_file,
                    updated_at   = NOW()
            """)

            rows_affected = cursor.rowcount
            self.conn.commit()

            logger.info(
                f"Upserted {rows_affected} rows from {source_file} "
                f"({len(events)} input events)"
            )

            return rows_affected

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to upsert batch from {source_file}: {e}")
            raise

    def ensure_partition_exists(self, target_date: datetime) -> None:
        """
        Create partition for target month if it doesn't exist
        Call this before ingesting data for a new month
        """
        partition_start = target_date.replace(day=1)
        next_month = (partition_start.month % 12) + 1
        next_year = partition_start.year + (1 if next_month == 1 else 0)
        partition_end = partition_start.replace(year=next_year, month=next_month)

        partition_name = f"github_events_{partition_start.strftime('%Y_%m')}"

        cursor = self.conn.cursor()
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS raw.{partition_name}
            PARTITION OF raw.github_events
            FOR VALUES FROM ('{partition_start.date()}') TO ('{partition_end.date()}')
        """)
        self.conn.commit()

        logger.info(f"Ensured partition exists: raw.{partition_name}")


class BigQueryRawLoader:
    """
    BigQuery implementation using staging table + MERGE pattern
    Optimized for large-scale batch processing
    """

    def __init__(self, client, project_id: str, dataset_id: str = 'raw'):
        """
        Args:
            client: google.cloud.bigquery.Client instance
            project_id: GCP project ID
            dataset_id: BigQuery dataset name (default: 'raw')
        """
        from google.cloud import bigquery

        self.client = client
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_id = f"{project_id}.{dataset_id}.github_events"
        self.staging_table_id = f"{project_id}.{dataset_id}.github_events_staging"

    def _transform_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Transform GitHub event JSON to BigQuery row format"""
        created_at = datetime.fromisoformat(
            event['created_at'].replace('Z', '+00:00')
        )

        return {
            'event_id': event['id'],
            'event_type': event['type'],
            'created_at': created_at.isoformat(),
            'actor_id': event.get('actor', {}).get('id'),
            'actor_login': event.get('actor', {}).get('login'),
            'repo_id': str(event.get('repo', {}).get('id')) if event.get('repo', {}).get('id') else None,
            'repo_name': event.get('repo', {}).get('name'),
            'org_id': event.get('org', {}).get('id'),
            'org_login': event.get('org', {}).get('login'),
            'is_public': event.get('public', True),
            'payload': event.get('payload', {}),  # BQ native JSON type
        }

    def upsert_batch(self, events: List[Dict[str, Any]], source_file: str) -> int:
        """
        Bulk upsert using staging table + MERGE pattern

        Pattern:
        1. Load into staging table
        2. MERGE with partition filter
        3. Drop staging table

        Args:
            events: List of parsed GitHub event dicts
            source_file: Source filename for lineage tracking

        Returns:
            Number of rows in staging (proxy for affected rows)
        """
        from google.cloud import bigquery

        if not events:
            return 0

        try:
            # Step 1: Prepare staging data
            rows = [
                {
                    **self._transform_event(event),
                    'source_file': source_file,
                    'ingested_at': datetime.now(timezone.utc).isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat(),
                }
                for event in events
            ]

            # Step 2: Load into staging table
            job_config = bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
                schema=[
                    bigquery.SchemaField("event_id", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("event_type", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
                    bigquery.SchemaField("actor_id", "STRING"),
                    bigquery.SchemaField("actor_login", "STRING"),
                    bigquery.SchemaField("repo_id", "STRING"),
                    bigquery.SchemaField("repo_name", "STRING"),
                    bigquery.SchemaField("org_id", "STRING"),
                    bigquery.SchemaField("org_login", "STRING"),
                    bigquery.SchemaField("is_public", "BOOL", mode="REQUIRED"),
                    bigquery.SchemaField("payload", "JSON"),
                    bigquery.SchemaField("source_file", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("ingested_at", "TIMESTAMP", mode="REQUIRED"),
                    bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED"),
                ]
            )

            load_job = self.client.load_table_from_json(
                rows,
                self.staging_table_id,
                job_config=job_config
            )
            load_job.result()  # Wait for completion

            logger.info(
                f"Loaded {len(rows)} rows into staging table "
                f"from {source_file}"
            )

            # Step 3: MERGE from staging to main table
            merge_query = f"""
                MERGE INTO `{self.table_id}` AS target
                USING `{self.staging_table_id}` AS source
                ON  target.event_id = source.event_id
                AND DATE(target.created_at) = DATE(source.created_at)
                
                WHEN MATCHED THEN UPDATE SET
                    event_type   = source.event_type,
                    actor_id     = source.actor_id,
                    actor_login  = source.actor_login,
                    repo_id      = source.repo_id,
                    repo_name    = source.repo_name,
                    org_id       = source.org_id,
                    org_login    = source.org_login,
                    is_public    = source.is_public,
                    payload      = source.payload,
                    source_file  = source.source_file,
                    updated_at   = CURRENT_TIMESTAMP()
                
                WHEN NOT MATCHED THEN INSERT (
                    event_id, event_type, created_at,
                    actor_id, actor_login, repo_id, repo_name,
                    org_id, org_login, is_public, payload,
                    source_file, ingested_at, updated_at
                ) VALUES (
                    source.event_id, source.event_type, source.created_at,
                    source.actor_id, source.actor_login, source.repo_id, source.repo_name,
                    source.org_id, source.org_login, source.is_public, source.payload,
                    source.source_file, source.ingested_at, source.updated_at
                )
            """

            merge_job = self.client.query(merge_query)
            merge_job.result()  # Wait for completion

            logger.info(
                f"MERGE completed for {source_file}. "
                f"Query job: {merge_job.job_id}"
            )

            # Step 4: Cleanup staging table
            self.client.delete_table(self.staging_table_id, not_found_ok=True)

            return len(rows)

        except Exception as e:
            logger.error(f"Failed to upsert batch to BigQuery: {e}")
            # Cleanup staging table on error
            self.client.delete_table(self.staging_table_id, not_found_ok=True)
            raise


# ============================================================================
# Usage Examples
# ============================================================================

def example_postgres_usage():
    """Example: Load GitHub Archive file into Postgres"""
    import psycopg2

    # Setup connection
    conn = psycopg2.connect(
        host="localhost",
        database="github_archive",
        user="postgres",
        password="postgres"
    )

    loader = PostgresRawLoader(conn)

    # Load a .json.gz file from GitHub Archive
    file_path = Path("data/2026-03-13-10.json.gz")

    # Parse events
    events = []
    with gzip.open(file_path, 'rt') as f:
        for line in f:
            events.append(json.loads(line))

    # Ensure partition exists for this month
    loader.ensure_partition_exists(datetime(2026, 3, 13))

    # Upsert batch
    rows_affected = loader.upsert_batch(events, file_path.name)

    print(f"Loaded {rows_affected} rows from {file_path.name}")

    conn.close()


def example_bigquery_usage():
    """Example: Load GitHub Archive file into BigQuery"""
    from google.cloud import bigquery

    # Setup client
    client = bigquery.Client(project="your-project-id")

    loader = BigQueryRawLoader(
        client=client,
        project_id="your-project-id",
        dataset_id="raw"
    )

    # Load a .json.gz file from GitHub Archive
    file_path = Path("data/2026-03-13-10.json.gz")

    # Parse events
    events = []
    with gzip.open(file_path, 'rt') as f:
        for line in f:
            events.append(json.loads(line))

    # Upsert batch
    rows_affected = loader.upsert_batch(events, file_path.name)

    print(f"Loaded {rows_affected} rows from {file_path.name}")


if __name__ == "__main__":
    # Run examples
    logging.basicConfig(level=logging.INFO)

    # Uncomment the one you want to test:
    # example_postgres_usage()
    # example_bigquery_usage()
    pass

