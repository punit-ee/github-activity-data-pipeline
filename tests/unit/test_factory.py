"""Unit tests for GitHubArchiveClientFactory."""
import unittest
from unittest.mock import Mock

from ingestion.config import GitHubArchiveConfig
from ingestion.factory import GitHubArchiveClientFactory
from ingestion.github_archive_client import GitHubArchiveClient


class TestGitHubArchiveClientFactory(unittest.TestCase):
    """Test GitHubArchiveClientFactory."""

    def test_create_default(self):
        """Test creating default client."""
        client = GitHubArchiveClientFactory.create_default()

        self.assertIsInstance(client, GitHubArchiveClient)
        self.assertEqual(client.timeout, (5.0, 30.0))
        client.close()

    def test_create_from_config(self):
        """Test creating client from config object."""
        config = GitHubArchiveConfig(
            connect_timeout=10.0,
            read_timeout=60.0,
        )

        client = GitHubArchiveClientFactory.create_from_config(config)

        self.assertIsInstance(client, GitHubArchiveClient)
        self.assertEqual(client.timeout, (10.0, 60.0))
        client.close()

    def test_create_from_invalid_config_raises(self):
        """Test creating client from invalid config raises error."""
        config = GitHubArchiveConfig(connect_timeout=-1.0)

        with self.assertRaises(ValueError):
            GitHubArchiveClientFactory.create_from_config(config)

    def test_create_for_production(self):
        """Test creating production client."""
        client = GitHubArchiveClientFactory.create_for_production()

        self.assertIsInstance(client, GitHubArchiveClient)
        self.assertEqual(client.timeout, (10.0, 60.0))
        client.close()

    def test_create_for_production_custom_timeouts(self):
        """Test creating production client with custom timeouts."""
        client = GitHubArchiveClientFactory.create_for_production(
            connect_timeout=20.0,
            read_timeout=120.0,
        )

        self.assertEqual(client.timeout, (20.0, 120.0))
        client.close()

    def test_create_for_testing(self):
        """Test creating testing client."""
        mock_session = Mock()
        client = GitHubArchiveClientFactory.create_for_testing(session=mock_session)

        self.assertIsInstance(client, GitHubArchiveClient)
        self.assertEqual(client.timeout, (1.0, 5.0))
        self.assertEqual(client.session, mock_session)

    def test_create_fast(self):
        """Test creating fast client."""
        client = GitHubArchiveClientFactory.create_fast()

        self.assertIsInstance(client, GitHubArchiveClient)
        self.assertEqual(client.timeout, (2.0, 10.0))
        client.close()

    def test_create_resilient(self):
        """Test creating resilient client."""
        client = GitHubArchiveClientFactory.create_resilient()

        self.assertIsInstance(client, GitHubArchiveClient)
        self.assertEqual(client.timeout, (15.0, 120.0))
        client.close()


if __name__ == "__main__":
    unittest.main()

