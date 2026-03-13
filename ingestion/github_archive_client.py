import logging
import re
from datetime import datetime
from typing import Optional, Tuple

import requests
from requests import Response, Session
from requests.adapters import HTTPAdapter
from requests.exceptions import HTTPError, RequestException, Timeout
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class GitHubArchiveClientError(Exception):
    """Base exception for GitHubArchiveClient failures."""


class GitHubArchiveDownloadError(GitHubArchiveClientError):
    """Raised when downloading GitHub Archive events fails."""


class GitHubArchiveClient:
    """
    Client responsible for interacting with GitHub Archive dataset.

    Uses an HTTP session with retries and a default timeout for safer,
    production-grade network access.
    """

    BASE_URL = "https://data.gharchive.org"
    DATE_HOUR_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{2}$")
    DEFAULT_TIMEOUT: Tuple[float, float] = (5.0, 30.0)
    USER_AGENT = "github-activity-data-pipeline/1.0"

    def __init__(
        self,
        timeout: Tuple[float, float] = DEFAULT_TIMEOUT,
        session: Optional[Session] = None,
    ) -> None:
        self.timeout = self._validate_timeout(timeout)
        self.session = session or self._build_session()

    @classmethod
    def _build_session(cls) -> Session:
        """Build a requests session configured with retry strategy."""
        retry = Retry(
            total=3,
            connect=3,
            read=3,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)

        session = requests.Session()
        session.headers.update({"User-Agent": cls.USER_AGENT})
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    @staticmethod
    def _validate_timeout(timeout: Tuple[float, float]) -> Tuple[float, float]:
        """Ensure timeout is a (connect, read) pair with positive values."""
        if len(timeout) != 2:
            raise ValueError("timeout must be a tuple of (connect_timeout, read_timeout)")

        connect_timeout, read_timeout = timeout
        if connect_timeout <= 0 or read_timeout <= 0:
            raise ValueError("timeout values must be positive")

        return timeout

    def build_url(self, date_hour: str) -> str:
        """
        Build download URL for a given hour.

        Example:
        2026-03-13-10 -> https://data.gharchive.org/2026-03-13-10.json.gz
        """
        self._validate_date_hour(date_hour)
        return f"{self.BASE_URL}/{date_hour}.json.gz"

    def _validate_date_hour(self, date_hour: str) -> None:
        """Validate date hour format YYYY-MM-DD-HH and calendar correctness."""
        if not self.DATE_HOUR_PATTERN.fullmatch(date_hour):
            raise ValueError(
                "date_hour must be in 'YYYY-MM-DD-HH' format, "
                f"received '{date_hour}'"
            )

        try:
            datetime.strptime(date_hour, "%Y-%m-%d-%H")
        except ValueError as exc:
            raise ValueError(f"date_hour is not a valid calendar hour: '{date_hour}'") from exc

    def download_events(self, date_hour: str) -> Response:
        """
        Download GitHub events for a given hour.

        Raises:
            ValueError: If date_hour format is invalid.
            GitHubArchiveDownloadError: If the request fails or times out.
        """
        url = self.build_url(date_hour)

        logger.info("Downloading GitHub Archive events", extra={"url": url})
        try:
            response = self.session.get(url, stream=True, timeout=self.timeout)
            response.raise_for_status()
            logger.info(
                "GitHub Archive download request succeeded",
                extra={"url": url, "status_code": response.status_code},
            )
            return response
        except Timeout as exc:
            logger.exception("GitHub Archive request timed out", extra={"url": url})
            raise GitHubArchiveDownloadError(
                f"Timed out while downloading events from {url}"
            ) from exc
        except HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else "unknown"
            logger.exception(
                "GitHub Archive request returned HTTP error",
                extra={"url": url, "status_code": status_code},
            )
            raise GitHubArchiveDownloadError(
                f"HTTP error while downloading events from {url}: {status_code}"
            ) from exc
        except RequestException as exc:
            logger.exception(
                "GitHub Archive request failed due to network error",
                extra={"url": url},
            )
            raise GitHubArchiveDownloadError(
                f"Network error while downloading events from {url}"
            ) from exc

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self.session.close()

    def __enter__(self) -> "GitHubArchiveClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

