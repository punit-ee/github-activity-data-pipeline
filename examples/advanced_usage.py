"""
Advanced usage examples for GitHubArchiveClient.

This example demonstrates:
- Downloading multiple hours of data
- Custom timeout configuration
- Progress tracking
- Concurrent downloads with error handling
- Date range processing
"""
import gzip
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple

from ingestion import setup_logging, get_logger
from ingestion.github_archive_client import (
    GitHubArchiveClient,
    GitHubArchiveDownloadError,
)

# Setup centralized logging
setup_logging()
logger = get_logger(__name__)


def generate_date_hours(start_date: datetime, hours: int) -> List[str]:
    """
    Generate a list of date_hour strings for consecutive hours.

    Args:
        start_date: Starting datetime
        hours: Number of hours to generate

    Returns:
        List of date_hour strings in YYYY-MM-DD-HH format
    """
    return [
        (start_date + timedelta(hours=i)).strftime("%Y-%m-%d-%H")
        for i in range(hours)
    ]


def download_with_progress(
    date_hour: str,
    output_dir: Path,
    timeout: tuple = (5.0, 30.0),
) -> Optional[Path]:
    """
    Download a single hour with progress tracking.

    Args:
        date_hour: Hour to download
        output_dir: Output directory
        timeout: Connection and read timeout

    Returns:
        Path to downloaded file or None if failed
    """
    output_file = output_dir / f"{date_hour}.json.gz"

    if output_file.exists():
        logger.info(f"Skipping {date_hour} - already exists")
        return output_file

    try:
        with GitHubArchiveClient(timeout=timeout) as client:
            response = client.download_events(date_hour)

            total_size = 0
            with open(output_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
                        total_size += len(chunk)

            logger.info(
                f"Downloaded {date_hour}: {total_size / (1024 * 1024):.2f} MB"
            )
            return output_file

    except GitHubArchiveDownloadError as e:
        logger.error(f"Failed to download {date_hour}: {e}")
        return None
    except Exception as e:
        logger.exception(f"Unexpected error downloading {date_hour}: {e}")
        return None


def download_date_range_concurrent(
    start_date: datetime,
    hours: int,
    output_dir: Path,
    max_workers: int = 3,
) -> dict:
    """
    Download multiple hours concurrently with error tracking.

    Args:
        start_date: Starting datetime
        hours: Number of hours to download
        output_dir: Output directory
        max_workers: Maximum concurrent downloads

    Returns:
        Dictionary with success and failure counts
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    date_hours = generate_date_hours(start_date, hours)

    results = {"success": 0, "failed": 0, "skipped": 0}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all download tasks
        future_to_date = {
            executor.submit(download_with_progress, dh, output_dir): dh
            for dh in date_hours
        }

        # Process completed tasks
        for future in as_completed(future_to_date):
            date_hour = future_to_date[future]
            try:
                result = future.result()
                if result:
                    results["success"] += 1
                else:
                    results["failed"] += 1
            except Exception as e:
                logger.exception(f"Unexpected error processing {date_hour}: {e}")
                results["failed"] += 1

    logger.info(f"Download summary: {results}")
    return results


def analyze_downloaded_file(file_path: Path, limit: int = 10) -> None:
    """
    Analyze a downloaded GitHub Archive file.

    Args:
        file_path: Path to the .json.gz file
        limit: Number of events to display
    """
    logger.info(f"Analyzing {file_path}")

    event_types = {}

    with gzip.open(file_path, "rt", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if idx >= limit:
                break

            try:
                event = json.loads(line)
                event_type = event.get("type", "Unknown")
                event_types[event_type] = event_types.get(event_type, 0) + 1

                if idx < 3:  # Show first 3 events
                    logger.info(
                        f"Event {idx + 1}: {event_type} by {event.get('actor', {}).get('login', 'unknown')}"
                    )
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse line {idx}: {e}")

    logger.info(f"Event type distribution (first {limit} events): {event_types}")


if __name__ == "__main__":
    # Example 1: Download last 24 hours of data
    logger.info("=== Example 1: Download last 24 hours ===")
    start = datetime(2026, 3, 13, 0)
    output_dir = Path("./data/batch_download")

    results = download_date_range_concurrent(
        start_date=start,
        hours=24,
        output_dir=output_dir,
        max_workers=5,
    )

    # Example 2: Download with custom timeout
    logger.info("\n=== Example 2: Custom timeout configuration ===")
    custom_output = Path("./data/custom_timeout")
    custom_output.mkdir(parents=True, exist_ok=True)

    with GitHubArchiveClient(timeout=(10.0, 60.0)) as client:
        try:
            response = client.download_events("2026-03-13-10")
            output_file = custom_output / "2026-03-13-10.json.gz"

            with open(output_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            logger.info(f"Downloaded with custom timeout to {output_file}")

            # Analyze the downloaded file
            analyze_downloaded_file(output_file)

        except GitHubArchiveDownloadError as e:
            logger.error(f"Download failed: {e}")

    # Example 3: Single hour download with error handling
    logger.info("\n=== Example 3: Single hour with comprehensive error handling ===")
    single_output = Path("./data/single")
    result = download_with_progress("2026-03-13-15", single_output)

    if result:
        logger.info(f"Successfully downloaded to {result}")
    else:
        logger.error("Download failed")

