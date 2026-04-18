"""
Database abstraction layer for data ingestion.

Design Pattern: Strategy Pattern
Production-ready with RawTableLoader for optimal upsert performance.
"""
import gzip
import json
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from ingestion.raw_table_loader import PostgresRawLoader, BigQueryRawLoader

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
        self,
        file_path: Path,
        table_name: str = "github_events",
        batch_size: int = 1000,
    ) -> IngestionMetrics:
        """
        Ingest data from a JSONL gzip file into raw.github_events table.

        Args:
            file_path: Path to .json.gz file
            table_name: Target table name (default: github_events -> raw.github_events)
            batch_size: Ignored (kept for compatibility)

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
    """PostgreSQL database backend using production-ready raw table loader."""

    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        schema: str = "public",
        use_pooling: bool = False,
        pool_size: int = 5,
    ):
        """
        Initialize PostgreSQL backend.

        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Username
            password: Password
            schema: Schema name (ignored, always uses raw for github_events)
            use_pooling: Enable connection pooling for parallel tasks (default: False)
            pool_size: Maximum pool size if pooling enabled (default: 5)
        """
        try:
            import psycopg2
            from psycopg2 import pool as pg_pool
        except ImportError:
            raise ImportError(
                "psycopg2-binary is required for PostgreSQL. "
                "Install with: pip install psycopg2-binary"
            )

        self.schema = schema
        self.use_pooling = use_pooling
        
        if use_pooling:
            # Use connection pool for parallel task execution
            self.pool = pg_pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=pool_size,
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
            )
            self.connection = None
            logger.info(
                "Initialized PostgreSQL backend with connection pool",
                extra={"host": host, "database": database, "pool_size": pool_size},
            )
        else:
            # Single connection (safe for sequential tasks only)
            self.pool = None
            self.connection = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
            )
            self.connection.autocommit = False
            logger.info(
                "Initialized PostgreSQL backend with single connection",
                extra={"host": host, "database": database},
            )
        
        # Note: raw_loader is created per-operation to use correct connection
        self._connection_params = {
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password,
        }

    def _get_connection(self):
        """Get a connection from pool or return the single connection."""
        if self.use_pooling:
            import psycopg2
            return self.pool.getconn()
        return self.connection

    def _return_connection(self, conn):
        """Return connection to pool or do nothing for single connection."""
        if self.use_pooling:
            self.pool.putconn(conn)

    def ingest_from_file(
        self,
        file_path: Path,
        table_name: str = "github_events",
        batch_size: int = 1000,
    ) -> IngestionMetrics:
        """
        Ingest data from JSONL gzip file into raw.github_events table.
        
        Uses production-ready PostgresRawLoader with staging table pattern
        for optimal performance (15K+ rows/sec) and idempotent upserts.
        
        Thread-safe when use_pooling=True.
        """
        import time

        metrics = IngestionMetrics(table_name="raw.github_events")
        start_time = time.time()

        if not file_path.exists():
            metrics.error_message = f"File not found: {file_path}"
            return metrics

        conn = None
        try:
            # Get connection (from pool or single)
            conn = self._get_connection()
            conn.autocommit = False
            
            # Create loader with this specific connection
            raw_loader = PostgresRawLoader(conn)
            
            # Parse events from compressed file
            events: List[Dict[str, Any]] = []
            with gzip.open(file_path, "rt", encoding="utf-8") as f:
                for line in f:
                    metrics.bytes_processed += len(line.encode("utf-8"))
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        metrics.rows_failed += 1

            # Extract datetime from filename for partition: YYYY-MM-DD-H.json.gz
            source_file = file_path.name
            match = re.match(r"^(\d{4}-\d{2}-\d{2})-(\d{1,2})\.json\.gz$", source_file)
            if match:
                partition_dt = datetime.strptime(f"{match.group(1)}-{match.group(2)}", "%Y-%m-%d-%H")
                raw_loader.ensure_partition_exists(partition_dt)

            # Upsert batch using raw loader
            rows = raw_loader.upsert_batch(events, source_file=source_file)
            metrics.rows_inserted = rows
            metrics.success = True
            metrics.duration_seconds = time.time() - start_time

            logger.info(
                "PostgreSQL ingestion completed",
                extra={
                    "table": "raw.github_events",
                    "rows": metrics.rows_inserted,
                    "failed": metrics.rows_failed,
                    "duration": metrics.duration_seconds,
                    "pooled": self.use_pooling,
                },
            )

        except Exception as e:
            if conn:
                conn.rollback()
            metrics.error_message = str(e)
            logger.exception("PostgreSQL ingestion failed", extra={"error": str(e)})
        finally:
            if conn:
                self._return_connection(conn)

        return metrics

    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a query and return results. Thread-safe when pooling enabled."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            cursor.close()
            return results
        finally:
            self._return_connection(conn)

    def get_last_processed_hour(self) -> Optional[datetime]:
        """
        Query raw.github_events to find the most recent source_file processed.
        Thread-safe when pooling enabled.
        
        Returns:
            Datetime of the last processed hour, or None if table is empty.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT source_file 
                FROM raw.github_events 
                ORDER BY created_at DESC 
                LIMIT 1
            """)
            result = cursor.fetchone()
            cursor.close()
            
            if result and result[0]:
                # Parse format: YYYY-MM-DD-H.json.gz
                source_file = result[0].replace('.json.gz', '')
                logger.info(f"Last processed source file: {result[0]}")
                return datetime.strptime(source_file, "%Y-%m-%d-%H")
                
        except Exception as e:
            logger.warning(f"Could not query last processed hour: {e}")
        finally:
            self._return_connection(conn)
        
        return None

    def table_exists(self, table_name: str) -> bool:
        """Check if table exists in PostgreSQL. Thread-safe when pooling enabled."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            # Always check in raw schema for github_events
            schema = "raw" if table_name == "github_events" else self.schema
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = %s AND table_name = %s
                )
                """,
                (schema, table_name),
            )
            exists = cursor.fetchone()[0]
            cursor.close()
            return exists
        finally:
            self._return_connection(conn)

    def close(self) -> None:
        """Close PostgreSQL connection or connection pool."""
        if self.use_pooling and hasattr(self, "pool") and self.pool:
            self.pool.closeall()
            logger.info("Closed PostgreSQL connection pool")
        elif hasattr(self, "connection") and self.connection:
            self.connection.close()
            logger.info("Closed PostgreSQL connection")


class BigQueryBackend(DatabaseBackend):
    """BigQuery database backend using production-ready raw table loader."""

    def __init__(
        self,
        project_id: str,
        dataset_id: str = "raw",
        location: str = "US",
    ):
        """
        Initialize BigQuery backend.

        Args:
            project_id: GCP project ID
            dataset_id: BigQuery dataset ID (default: raw)
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
        self.raw_loader = BigQueryRawLoader(
            client=self.client,
            project_id=project_id,
            dataset_id=dataset_id,
        )

        # Ensure dataset exists
        dataset_full_id = f"{project_id}.{dataset_id}"
        try:
            self.client.get_dataset(dataset_full_id)
        except Exception:
            dataset = bigquery.Dataset(dataset_full_id)
            dataset.location = location
            self.client.create_dataset(dataset)
            logger.info(f"Created BigQuery dataset: {dataset_id}")

        logger.info(
            "Initialized BigQuery backend with raw table loader",
            extra={"project": project_id, "dataset": dataset_id},
        )

    def ingest_from_file(
        self,
        file_path: Path,
        table_name: str = "github_events",
        batch_size: int = 1000,
    ) -> IngestionMetrics:
        """
        Ingest data from JSONL gzip file into raw.github_events table.

        Uses production-ready BigQueryRawLoader with staging + MERGE pattern
        for optimal performance (28K+ rows/sec) and idempotent upserts.
        """
        import time

        metrics = IngestionMetrics(table_name=f"{self.dataset_id}.github_events")
        start_time = time.time()

        if not file_path.exists():
            metrics.error_message = f"File not found: {file_path}"
            return metrics

        try:
            # Parse events from compressed file
            events: List[Dict[str, Any]] = []
            with gzip.open(file_path, "rt", encoding="utf-8") as f:
                for line in f:
                    metrics.bytes_processed += len(line.encode("utf-8"))
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        metrics.rows_failed += 1

            # Upsert batch using raw loader
            rows = self.raw_loader.upsert_batch(events, source_file=file_path.name)
            metrics.rows_inserted = rows
            metrics.success = True
            metrics.duration_seconds = time.time() - start_time

            logger.info(
                "BigQuery ingestion completed",
                extra={
                    "table": f"{self.dataset_id}.github_events",
                    "rows": metrics.rows_inserted,
                    "failed": metrics.rows_failed,
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

    def get_last_processed_hour(self) -> Optional[datetime]:
        """
        Query raw.github_events to find the most recent source_file processed.

        Returns:
            Datetime of the last processed hour, or None if table is empty.
        """
        try:
            query = f"""
                SELECT source_file 
                FROM `{self.project_id}.{self.dataset_id}.github_events` 
                ORDER BY created_at DESC 
                LIMIT 1
            """
            result = self.client.query(query).result()

            for row in result:
                source_file = row.source_file.replace('.json.gz', '')
                logger.info(f"Last processed source file: {row.source_file}")
                return datetime.strptime(source_file, "%Y-%m-%d-%H")

        except Exception as e:
            logger.warning(f"Could not query last processed hour: {e}")

        return None

    def table_exists(self, table_name: str) -> bool:
        """Check if table exists in BigQuery."""
        try:
            table_id = f"{self.project_id}.{self.dataset_id}.{table_name}"
            self.client.get_table(table_id)
            return True
        except Exception:
            return False

    def close(self) -> None:
        """Close BigQuery client."""
        if hasattr(self, "client"):
            self.client.close()

