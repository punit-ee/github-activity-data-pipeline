"""
Production-ready usage example with structured logging and monitoring.

This example demonstrates:
- Structured JSON logging
- Metrics collection
- Retry logic with exponential backoff
- Health checks
- Configuration management
"""
import json
import logging
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from ingestion.github_archive_client import (
    GitHubArchiveClient,
    GitHubArchiveDownloadError,
)


# Structured logging setup
class JsonFormatter(logging.Formatter):
    """Format logs as JSON for production systems."""

    def format(self, record):
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data)


def setup_production_logging(level: int = logging.INFO) -> None:
    """Configure production-grade structured logging."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)


@dataclass
class DownloadMetrics:
    """Metrics for monitoring downloads."""

    date_hour: str
    start_time: float
    end_time: Optional[float] = None
    file_size_bytes: int = 0
    success: bool = False
    error_message: Optional[str] = None
    retry_count: int = 0

    @property
    def duration_seconds(self) -> float:
        """Calculate download duration."""
        if self.end_time:
            return self.end_time - self.start_time
        return 0.0

    @property
    def file_size_mb(self) -> float:
        """Get file size in MB."""
        return self.file_size_bytes / (1024 * 1024)

    def to_dict(self) -> dict:
        """Convert to dictionary for logging."""
        data = asdict(self)
        data["duration_seconds"] = self.duration_seconds
        data["file_size_mb"] = self.file_size_mb
        return data


class GitHubArchiveDownloader:
    """
    Production-ready downloader with metrics and retry logic.

    Design Patterns Applied:
    - Strategy Pattern: Configurable retry strategy
    - Template Method: Extensible download workflow
    - Dependency Injection: Client and logger injection
    """

    def __init__(
        self,
        output_dir: Path,
        client: Optional[GitHubArchiveClient] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize downloader.

        Args:
            output_dir: Directory for downloaded files
            client: GitHubArchiveClient instance (created if None)
            max_retries: Maximum retry attempts
            retry_delay: Initial retry delay (doubles each retry)
            logger: Logger instance
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.client = client or GitHubArchiveClient()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logger or logging.getLogger(__name__)

        self._should_close_client = client is None

    def download_with_retry(self, date_hour: str) -> DownloadMetrics:
        """
        Download with exponential backoff retry logic.

        Args:
            date_hour: Hour to download

        Returns:
            Metrics object with download results
        """
        metrics = DownloadMetrics(
            date_hour=date_hour,
            start_time=time.time(),
        )

        output_file = self.output_dir / f"{date_hour}.json.gz"

        # Check if already exists
        if output_file.exists():
            metrics.end_time = time.time()
            metrics.success = True
            metrics.file_size_bytes = output_file.stat().st_size
            self.logger.info(
                "File already exists",
                extra={"extra_data": {"date_hour": date_hour, "file": str(output_file)}},
            )
            return metrics

        # Retry loop
        for attempt in range(self.max_retries):
            try:
                self._log_attempt(date_hour, attempt)
                self._download_to_file(date_hour, output_file)

                # Success
                metrics.end_time = time.time()
                metrics.success = True
                metrics.file_size_bytes = output_file.stat().st_size
                metrics.retry_count = attempt

                self._log_success(metrics)
                return metrics

            except GitHubArchiveDownloadError as e:
                metrics.error_message = str(e)
                self._handle_retry(attempt, date_hour, e)

            except Exception as e:
                metrics.error_message = f"Unexpected error: {e}"
                self.logger.exception(
                    "Unexpected download error",
                    extra={"extra_data": {"date_hour": date_hour, "attempt": attempt}},
                )
                break

        # All retries failed
        metrics.end_time = time.time()
        metrics.retry_count = self.max_retries
        self._log_failure(metrics)
        return metrics

    def _download_to_file(self, date_hour: str, output_file: Path) -> None:
        """Execute the actual download."""
        response = self.client.download_events(date_hour)

        with open(output_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

    def _log_attempt(self, date_hour: str, attempt: int) -> None:
        """Log download attempt."""
        self.logger.info(
            "Starting download attempt",
            extra={
                "extra_data": {
                    "date_hour": date_hour,
                    "attempt": attempt + 1,
                    "max_retries": self.max_retries,
                }
            },
        )

    def _handle_retry(
        self, attempt: int, date_hour: str, error: Exception
    ) -> None:
        """Handle retry logic with exponential backoff."""
        if attempt < self.max_retries - 1:
            delay = self.retry_delay * (2 ** attempt)
            self.logger.warning(
                "Download failed, retrying",
                extra={
                    "extra_data": {
                        "date_hour": date_hour,
                        "attempt": attempt + 1,
                        "error": str(error),
                        "retry_in_seconds": delay,
                    }
                },
            )
            time.sleep(delay)
        else:
            self.logger.error(
                "All retry attempts exhausted",
                extra={
                    "extra_data": {
                        "date_hour": date_hour,
                        "error": str(error),
                    }
                },
            )

    def _log_success(self, metrics: DownloadMetrics) -> None:
        """Log successful download."""
        self.logger.info(
            "Download completed successfully",
            extra={"extra_data": metrics.to_dict()},
        )

    def _log_failure(self, metrics: DownloadMetrics) -> None:
        """Log failed download."""
        self.logger.error(
            "Download failed after all retries",
            extra={"extra_data": metrics.to_dict()},
        )

    def health_check(self) -> bool:
        """
        Perform health check by attempting to build a URL.

        Returns:
            True if client is healthy
        """
        try:
            # Simple validation check
            test_date = "2026-01-01-00"
            url = self.client.build_url(test_date)
            self.logger.info("Health check passed", extra={"extra_data": {"url": url}})
            return True
        except Exception as e:
            self.logger.error(
                "Health check failed",
                extra={"extra_data": {"error": str(e)}},
            )
            return False

    def close(self) -> None:
        """Clean up resources."""
        if self._should_close_client:
            self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == "__main__":
    # Setup production logging
    setup_production_logging()

    logger = logging.getLogger(__name__)
    logger.info(
        "Starting production download job",
        extra={"extra_data": {"job_type": "github_archive_download"}},
    )

    # Create downloader with custom configuration
    output_directory = Path("./data/production")

    with GitHubArchiveDownloader(
        output_dir=output_directory,
        max_retries=5,
        retry_delay=2.0,
    ) as downloader:
        # Health check before starting
        if not downloader.health_check():
            logger.error("Health check failed, aborting job")
            sys.exit(1)

        # Download multiple hours
        date_hours = [
            "2026-03-13-10",
            "2026-03-13-11",
            "2026-03-13-12",
        ]

        all_metrics = []
        for date_hour in date_hours:
            metrics = downloader.download_with_retry(date_hour)
            all_metrics.append(metrics)

        # Summary
        successful = sum(1 for m in all_metrics if m.success)
        failed = len(all_metrics) - successful
        total_mb = sum(m.file_size_mb for m in all_metrics)

        logger.info(
            "Job completed",
            extra={
                "extra_data": {
                    "total_files": len(all_metrics),
                    "successful": successful,
                    "failed": failed,
                    "total_size_mb": round(total_mb, 2),
                }
            },
        )

        # Exit with error code if any downloads failed
        sys.exit(0 if failed == 0 else 1)

