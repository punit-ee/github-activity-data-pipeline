"""
Basic usage example for GitHubArchiveClient.

This example demonstrates:
- Simple download of GitHub Archive events
- Basic error handling
- Streaming response to file
"""
import logging
from pathlib import Path

from ingestion.github_archive_client import (
    GitHubArchiveClient,
    GitHubArchiveDownloadError,
)

# Configure logging to see client activity
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def download_github_events(date_hour: str, output_dir: Path) -> None:
    """
    Download GitHub Archive events for a specific hour.

    Args:
        date_hour: Hour to download in format YYYY-MM-DD-HH
        output_dir: Directory to save the downloaded file
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{date_hour}.json.gz"

    logger.info(f"Starting download for {date_hour}")

    try:
        # Use context manager for automatic cleanup
        with GitHubArchiveClient() as client:
            response = client.download_events(date_hour)

            # Stream the response to avoid loading everything in memory
            with open(output_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):  # 1MB chunks
                    if chunk:
                        f.write(chunk)

            logger.info(f"Successfully downloaded events to {output_file}")

    except ValueError as e:
        logger.error(f"Invalid date_hour format: {e}")
        raise
    except GitHubArchiveDownloadError as e:
        logger.error(f"Failed to download events: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during download: {e}")
        raise


if __name__ == "__main__":
    # Example: Download events from March 13, 2026, 10:00 AM
    output_directory = Path("./data")
    date_hour_to_download = "2026-03-13-10"

    download_github_events(date_hour_to_download, output_directory)

