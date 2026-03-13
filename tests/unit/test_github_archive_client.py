import unittest
from unittest.mock import Mock, patch

from requests import Response
from requests.exceptions import HTTPError, Timeout

from ingestion.github_archive_client import (
    GitHubArchiveClient,
    GitHubArchiveDownloadError,
)


class GitHubArchiveClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.logger_patcher = patch("ingestion.github_archive_client.logger")
        self.logger_patcher.start()

    def tearDown(self) -> None:
        self.logger_patcher.stop()

    def test_build_url_valid(self) -> None:
        client = GitHubArchiveClient(session=Mock())
        self.assertEqual(
            client.build_url("2026-03-13-10"),
            "https://data.gharchive.org/2026-03-13-10.json.gz",
        )

    def test_build_url_invalid_date_hour(self) -> None:
        client = GitHubArchiveClient(session=Mock())
        with self.assertRaises(ValueError):
            client.build_url("2026-13-40-25")

    def test_download_events_success(self) -> None:
        response = Response()
        response.status_code = 200

        mock_session = Mock()
        mock_session.get.return_value = response

        client = GitHubArchiveClient(session=mock_session)
        result = client.download_events("2026-03-13-10")

        self.assertEqual(result.status_code, 200)
        mock_session.get.assert_called_once()

    def test_download_events_timeout_is_wrapped(self) -> None:
        mock_session = Mock()
        mock_session.get.side_effect = Timeout("timed out")

        client = GitHubArchiveClient(session=mock_session)
        with self.assertRaises(GitHubArchiveDownloadError):
            client.download_events("2026-03-13-10")

    def test_download_events_http_error_is_wrapped(self) -> None:
        response = Response()
        response.status_code = 503

        http_error = HTTPError(response=response)

        mock_session = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = http_error
        mock_session.get.return_value = mock_response

        client = GitHubArchiveClient(session=mock_session)
        with self.assertRaises(GitHubArchiveDownloadError):
            client.download_events("2026-03-13-10")


if __name__ == "__main__":
    unittest.main()
