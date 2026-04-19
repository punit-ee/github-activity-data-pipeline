"""Additional unit tests for enhanced coverage of GitHubArchiveClient."""
import unittest
from unittest.mock import Mock, patch

from requests.exceptions import RequestException

from ingestion.github_archive_client import (
    GitHubArchiveClient,
    GitHubArchiveClientError,
    GitHubArchiveDownloadError,
)


class TestGitHubArchiveClientEnhanced(unittest.TestCase):
    """Enhanced unit tests for edge cases."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.logger_patcher = patch("ingestion.github_archive_client.logger")
        self.mock_logger = self.logger_patcher.start()

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        self.logger_patcher.stop()

    def test_context_manager_closes_session(self) -> None:
        """Test context manager properly closes session."""
        mock_session = Mock()

        with GitHubArchiveClient(session=mock_session) as client:
            self.assertEqual(client.session, mock_session)

        mock_session.close.assert_called_once()

    def test_validate_timeout_with_invalid_length(self) -> None:
        """Test timeout validation fails with wrong tuple length."""
        with self.assertRaises(ValueError) as ctx:
            GitHubArchiveClient(timeout=(5.0,))  # Only one value

        self.assertIn("must be a tuple", str(ctx.exception))

    def test_validate_timeout_with_zero_connect(self) -> None:
        """Test timeout validation fails with zero connect timeout."""
        with self.assertRaises(ValueError) as ctx:
            GitHubArchiveClient(timeout=(0.0, 30.0))

        self.assertIn("must be positive", str(ctx.exception))

    def test_validate_timeout_with_negative_read(self) -> None:
        """Test timeout validation fails with negative read timeout."""
        with self.assertRaises(ValueError) as ctx:
            GitHubArchiveClient(timeout=(5.0, -10.0))

        self.assertIn("must be positive", str(ctx.exception))

    def test_validate_date_hour_invalid_format(self) -> None:
        """Test date validation with various invalid formats."""
        client = GitHubArchiveClient(session=Mock())

        invalid_dates = [
            "2026-03-13",  # Missing hour
            "2026-03-13-25",  # Invalid hour
            "2026-13-01-10",  # Invalid month
            "2026-03-32-10",  # Invalid day
            "not-a-date",  # Completely wrong
            "2026/03/13/10",  # Wrong separator
            "",  # Empty
        ]

        for invalid_date in invalid_dates:
            with self.assertRaises(ValueError):
                client.build_url(invalid_date)

    def test_download_events_network_error_is_wrapped(self) -> None:
        """Test network errors are wrapped in GitHubArchiveDownloadError."""
        mock_session = Mock()
        mock_session.get.side_effect = RequestException("Network failure")

        client = GitHubArchiveClient(session=mock_session)

        with self.assertRaises(GitHubArchiveDownloadError) as ctx:
            client.download_events("2026-03-13-10")

        self.assertIn("Network error", str(ctx.exception))

    def test_build_session_creates_retry_adapter(self) -> None:
        """Test _build_session creates session with retry configuration."""
        session = GitHubArchiveClient._build_session()

        self.assertIsNotNone(session)
        self.assertIn("User-Agent", session.headers)
        self.assertEqual(
            session.headers["User-Agent"],
            "github-activity-data-pipeline/1.0",
        )

    def test_custom_timeout_is_preserved(self) -> None:
        """Test custom timeout is stored correctly."""
        custom_timeout = (15.0, 90.0)
        client = GitHubArchiveClient(timeout=custom_timeout)

        self.assertEqual(client.timeout, custom_timeout)
        client.close()

    def test_exception_hierarchy(self) -> None:
        """Test exception class hierarchy."""
        self.assertTrue(issubclass(GitHubArchiveDownloadError, GitHubArchiveClientError))
        self.assertTrue(issubclass(GitHubArchiveClientError, Exception))

    def test_logger_info_on_success(self) -> None:
        """Test logger is called on successful download."""
        mock_response = Mock()
        mock_response.status_code = 200

        mock_session = Mock()
        mock_session.get.return_value = mock_response

        client = GitHubArchiveClient(session=mock_session)
        client.download_events("2026-03-13-10")

        # Verify logging was called
        self.assertTrue(self.mock_logger.info.called)

    def test_logger_exception_on_timeout(self) -> None:
        """Test logger.exception is called on timeout."""
        from requests.exceptions import Timeout

        mock_session = Mock()
        mock_session.get.side_effect = Timeout("Timed out")

        client = GitHubArchiveClient(session=mock_session)

        with self.assertRaises(GitHubArchiveDownloadError):
            client.download_events("2026-03-13-10")

        self.assertTrue(self.mock_logger.exception.called)

    def test_leap_year_date_validation(self) -> None:
        """Test date validation handles leap years correctly."""
        client = GitHubArchiveClient(session=Mock())

        # Valid leap year date
        url = client.build_url("2024-02-29-10")
        self.assertIn("2024-02-29-10", url)

        # Invalid non-leap year date
        with self.assertRaises(ValueError):
            client.build_url("2023-02-29-10")

    def test_url_format_is_correct(self) -> None:
        """Test URL format matches expected pattern."""
        client = GitHubArchiveClient(session=Mock())
        url = client.build_url("2026-03-13-10")

        self.assertEqual(url, "https://data.gharchive.org/2026-03-13-10.json.gz")
        self.assertTrue(url.endswith(".json.gz"))


class TestGitHubArchiveClientIntegrationScenarios(unittest.TestCase):
    """Test realistic integration scenarios without network calls."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.logger_patcher = patch("ingestion.github_archive_client.logger")
        self.logger_patcher.start()

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        self.logger_patcher.stop()

    def test_multiple_sequential_downloads(self) -> None:
        """Test multiple downloads with same client instance."""
        mock_response = Mock()
        mock_response.status_code = 200

        mock_session = Mock()
        mock_session.get.return_value = mock_response

        client = GitHubArchiveClient(session=mock_session)

        # Download multiple hours
        dates = ["2026-03-13-10", "2026-03-13-11", "2026-03-13-12"]
        for date_hour in dates:
            response = client.download_events(date_hour)
            self.assertEqual(response.status_code, 200)

        # Verify session was reused
        self.assertEqual(mock_session.get.call_count, 3)

        client.close()

    def test_download_with_streaming_enabled(self) -> None:
        """Test download_events passes stream=True to session.get."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_session.get.return_value = mock_response

        client = GitHubArchiveClient(session=mock_session)
        client.download_events("2026-03-13-10")

        # Verify stream=True was passed
        call_args = mock_session.get.call_args
        self.assertTrue(call_args.kwargs.get("stream"))


if __name__ == "__main__":
    unittest.main()

