import os
import unittest
from datetime import datetime, timedelta, timezone

from ingestion.github_archive_client import (
    GitHubArchiveClient,
    GitHubArchiveDownloadError,
)


RUN_INTEGRATION_TESTS = os.getenv("RUN_INTEGRATION_TESTS") == "1"


@unittest.skipUnless(
    RUN_INTEGRATION_TESTS,
    "Set RUN_INTEGRATION_TESTS=1 to run integration tests that call GitHub Archive.",
)
class GitHubArchiveClientIntegrationTests(unittest.TestCase):
    def test_download_events_returns_streaming_response(self) -> None:
        # Probe recent historical windows since the latest hour can lag publication.
        start_time = datetime.now(timezone.utc) - timedelta(hours=6)

        with GitHubArchiveClient(timeout=(3.0, 5.0)) as client:
            for offset_hours in range(0, 48):
                candidate = start_time - timedelta(hours=offset_hours)
                date_hour = candidate.strftime("%Y-%m-%d-%H")

                try:
                    response = client.download_events(date_hour)
                except GitHubArchiveDownloadError:
                    continue

                try:
                    first_chunk = next(response.iter_content(chunk_size=1024), b"")
                finally:
                    response.close()

                self.assertEqual(response.status_code, 200)
                self.assertTrue(first_chunk)
                return

        raise unittest.SkipTest(
            "No downloadable GitHub Archive hourly file found in the last 48 hours"
        )


if __name__ == "__main__":
    unittest.main()
