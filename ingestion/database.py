"""
Database abstraction layer for data ingestion.

Design Pattern: Strategy Pattern
Provides unified interface for different database backends (PostgreSQL, BigQuery).
"""
import gzip
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class IngestionMetrics:
    """Metrics for database ingestion."""

    rows_inserted: int = 0
    rows_failed: int = 0
    bytes_processed: int = 0
    duration_seconds: float = 0.0
    table_name: str = ""
    success: bool = False
    error_message: Optional[str] = None


class DatabaseBackend(ABC):
    """Abstract base class for database backends."""

    @abstractmethod
    def ingest_from_file(
        self, file_path: Path, table_name: str, batch_size: int = 1000
    ) -> IngestionMetrics:
        """
        Ingest data from a JSONL gzip file.

        Args:
            file_path: Path to .json.gz file
            table_name: Target table name
            batch_size: Number of rows per batch

        Returns:
            IngestionMetrics with ingestion results
        """
        pass

    @abstractmethod
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a query and return results."""
        pass

    @abstractmethod
    def table_exists(self, table_name: str) -> bool:
        """Check if table exists."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Clean up resources."""
        pass

    def __enter__(self) -> "DatabaseBackend":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


class DatabaseError(Exception):
    """Base exception for database operations."""
    pass


class PostgreSQLBackend(DatabaseBackend):
    """PostgreSQL database backend for local development."""

    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        schema: str = "public",
    ):
        """
        Initialize PostgreSQL backend.

        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Username
            password: Password
            schema: Schema name (default: public)
        """
        try:
            import psycopg2
            from psycopg2.extras import execute_batch
        except ImportError:
            raise ImportError(
                "psycopg2-binary is required for PostgreSQL. "
                "Install with: pip install psycopg2-binary"
            )

        self.schema = schema
        self.connection = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
        )
        self.connection.autocommit = False

        logger.info(
            "Initialized PostgreSQL backend",
            extra={"host": host, "database": database, "schema": schema},
        )

    def ingest_from_file(
        self, file_path: Path, table_name: str, batch_size: int = 1000
    ) -> IngestionMetrics:
        """Ingest data from JSONL gzip file into PostgreSQL."""
        import time
        import psycopg2.extras

        metrics = IngestionMetrics(table_name=table_name)
        start_time = time.time()

        if not file_path.exists():
            metrics.error_message = f"File not found: {file_path}"
            return metrics

        try:
            cursor = self.connection.cursor()

            # Create table if it doesn't exist (simplified schema)
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {self.schema}.{table_name} (
                id TEXT,
                type TEXT,
                actor JSONB,
                repo JSONB,
                payload JSONB,
                public BOOLEAN,
                created_at TIMESTAMP,
                org JSONB,
                raw_data JSONB,
                ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            cursor.execute(create_table_query)

            # Process file in batches
            batch = []
            with gzip.open(file_path, "rt", encoding="utf-8") as f:
                for line in f:
                    try:
                        event = json.loads(line)
                        metrics.bytes_processed += len(line.encode("utf-8"))

                        # Extract fields
                        row = (
                            event.get("id"),
                            event.get("type"),
                            json.dumps(event.get("actor", {})),
                            json.dumps(event.get("repo", {})),
                            json.dumps(event.get("payload", {})),
                            event.get("public"),
                            event.get("created_at"),
                            json.dumps(event.get("org")) if event.get("org") else None,
                            json.dumps(event),
                        )
                        batch.append(row)

                        if len(batch) >= batch_size:
                            self._insert_batch(cursor, table_name, batch)
                            metrics.rows_inserted += len(batch)
                            batch = []

                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse JSON line: {e}")
                        metrics.rows_failed += 1

            # Insert remaining rows
            if batch:
                self._insert_batch(cursor, table_name, batch)
                metrics.rows_inserted += len(batch)

            self.connection.commit()
            cursor.close()

            metrics.success = True
            metrics.duration_seconds = time.time() - start_time

            logger.info(
                "PostgreSQL ingestion completed",
                extra={
                    "table": table_name,
                    "rows": metrics.rows_inserted,
                    "duration": metrics.duration_seconds,
                },
            )

        except Exception as e:
            self.connection.rollback()
            metrics.error_message = str(e)
            logger.exception("PostgreSQL ingestion failed", extra={"error": str(e)})

        return metrics

    def _insert_batch(self, cursor, table_name: str, batch: List[tuple]) -> None:
        """Insert a batch of rows."""
        import psycopg2.extras

        insert_query = f"""
        INSERT INTO {self.schema}.{table_name}
        (id, type, actor, repo, payload, public, created_at, org, raw_data)
        VALUES (%s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s, %s::jsonb, %s::jsonb)
        """
        psycopg2.extras.execute_batch(cursor, insert_query, batch)

    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a query and return results."""
        cursor = self.connection.cursor()
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        cursor.close()
        return results

    def table_exists(self, table_name: str) -> bool:
        """Check if table exists in PostgreSQL."""
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = %s AND table_name = %s
            )
            """,
            (self.schema, table_name),
        )
        exists = cursor.fetchone()[0]
        cursor.close()
        return exists

    def close(self) -> None:
        """Close PostgreSQL connection."""
        if hasattr(self, "connection"):
            self.connection.close()


class BigQueryBackend(DatabaseBackend):
    """BigQuery database backend for production."""

    def __init__(
        self,
        project_id: str,
        dataset_id: str,
        location: str = "US",
    ):
        """
        Initialize BigQuery backend.

        Args:
            project_id: GCP project ID
            dataset_id: BigQuery dataset ID
            location: Dataset location (default: US)
        """
        try:
            from google.cloud import bigquery
        except ImportError:
            raise ImportError(
                "google-cloud-bigquery is required for BigQuery. "
                "Install with: pip install google-cloud-bigquery"
            )

        self.project_id = project_id
        self.dataset_id = dataset_id
        self.location = location
        self.client = bigquery.Client(project=project_id)

        # Ensure dataset exists
        dataset_ref = self.client.dataset(dataset_id)
        try:
            self.client.get_dataset(dataset_ref)
        except Exception:
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = location
            self.client.create_dataset(dataset)
            logger.info(f"Created BigQuery dataset: {dataset_id}")

        logger.info(
            "Initialized BigQuery backend",
            extra={"project": project_id, "dataset": dataset_id},
        )

    def ingest_from_file(
        self, file_path: Path, table_name: str, batch_size: int = 1000
    ) -> IngestionMetrics:
        """Ingest data from JSONL gzip file into BigQuery."""
        import time
        from google.cloud import bigquery

        metrics = IngestionMetrics(table_name=table_name)
        start_time = time.time()

        if not file_path.exists():
            metrics.error_message = f"File not found: {file_path}"
            return metrics

        try:
            table_ref = self.client.dataset(self.dataset_id).table(table_name)

            # Define schema
            schema = [
                bigquery.SchemaField("id", "STRING"),
                bigquery.SchemaField("type", "STRING"),
                bigquery.SchemaField("actor", "JSON"),
                bigquery.SchemaField("repo", "JSON"),
                bigquery.SchemaField("payload", "JSON"),
                bigquery.SchemaField("public", "BOOLEAN"),
                bigquery.SchemaField("created_at", "TIMESTAMP"),
                bigquery.SchemaField("org", "JSON"),
                bigquery.SchemaField("raw_data", "JSON"),
                bigquery.SchemaField(
                    "ingested_at", "TIMESTAMP", default_value_expression="CURRENT_TIMESTAMP()"
                ),
            ]

            # Create table if it doesn't exist
            try:
                self.client.get_table(table_ref)
            except Exception:
                table = bigquery.Table(table_ref, schema=schema)
                self.client.create_table(table)
                logger.info(f"Created BigQuery table: {table_name}")

            # Load data using BigQuery's native GZIP support
            job_config = bigquery.LoadJobConfig(
                source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
                schema=schema,
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            )

            with open(file_path, "rb") as f:
                load_job = self.client.load_table_from_file(
                    f, table_ref, job_config=job_config
                )

            # Wait for job to complete
            load_job.result()

            metrics.rows_inserted = load_job.output_rows or 0
            metrics.bytes_processed = file_path.stat().st_size
            metrics.success = True
            metrics.duration_seconds = time.time() - start_time

            logger.info(
                "BigQuery ingestion completed",
                extra={
                    "table": table_name,
                    "rows": metrics.rows_inserted,
                    "duration": metrics.duration_seconds,
                },
            )

        except Exception as e:
            metrics.error_message = str(e)
            logger.exception("BigQuery ingestion failed", extra={"error": str(e)})

        return metrics

    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a query and return results."""
        query_job = self.client.query(query)
        results = query_job.result()
        return [dict(row) for row in results]

    def table_exists(self, table_name: str) -> bool:
        """Check if table exists in BigQuery."""
        try:
            table_ref = self.client.dataset(self.dataset_id).table(table_name)
            self.client.get_table(table_ref)
            return True
        except Exception:
            return False

    def close(self) -> None:
        """Close BigQuery client."""
        if hasattr(self, "client"):
            self.client.close()

