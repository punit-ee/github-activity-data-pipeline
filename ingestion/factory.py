"""
Factory pattern for creating GitHubArchiveClient instances.

Design Pattern: Factory Pattern
Provides flexibility in client creation with different configurations.
"""
from typing import Optional, Tuple

from requests import Session

from ingestion.config import GitHubArchiveConfig
from ingestion.github_archive_client import GitHubArchiveClient


class GitHubArchiveClientFactory:
    """
    Factory for creating GitHubArchiveClient instances.

    Provides convenient methods for common configurations.
    """

    @staticmethod
    def create_default() -> GitHubArchiveClient:
        """Create client with default configuration."""
        return GitHubArchiveClient()

    @staticmethod
    def create_from_config(config: GitHubArchiveConfig) -> GitHubArchiveClient:
        """
        Create client from configuration object.

        Args:
            config: GitHubArchiveConfig instance

        Returns:
            Configured GitHubArchiveClient
        """
        config.validate()
        return GitHubArchiveClient(timeout=config.timeout)

    @staticmethod
    def create_for_production(
        connect_timeout: float = 10.0,
        read_timeout: float = 60.0,
    ) -> GitHubArchiveClient:
        """
        Create client optimized for production with longer timeouts.

        Args:
            connect_timeout: Connection timeout in seconds
            read_timeout: Read timeout in seconds

        Returns:
            Production-configured GitHubArchiveClient
        """
        return GitHubArchiveClient(timeout=(connect_timeout, read_timeout))

    @staticmethod
    def create_for_testing(
        session: Optional[Session] = None,
        timeout: tuple = (1.0, 5.0),
    ) -> GitHubArchiveClient:
        """
        Create client for testing with short timeouts.

        Args:
            session: Mock session for testing
            timeout: Short timeout for tests

        Returns:
            Test-configured GitHubArchiveClient
        """
        return GitHubArchiveClient(timeout=timeout, session=session)

    @staticmethod
    def create_fast() -> GitHubArchiveClient:
        """
        Create client with minimal timeouts for fast downloads.

        Use with caution - may fail on slow networks.

        Returns:
            Fast-configured GitHubArchiveClient
        """
        return GitHubArchiveClient(timeout=(2.0, 10.0))

    @staticmethod
    def create_resilient() -> GitHubArchiveClient:
        """
        Create client with extended timeouts for unreliable networks.

        Returns:
            Resilient-configured GitHubArchiveClient
        """
        return GitHubArchiveClient(timeout=(15.0, 120.0))

