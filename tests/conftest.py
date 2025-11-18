"""Shared pytest fixtures and configuration for all tests."""
from typing import Generator
from unittest import mock
import pytest
from gitlabber.method import CloneMethod
from gitlabber.auth import NoAuthProvider
from gitlabber.config import GitlabberSettings


# Test constants
TEST_URL = "http://gitlab.my.com/"
TEST_TOKEN = "MOCK_TOKEN"
TEST_AUTH_PROVIDER = NoAuthProvider()


@pytest.fixture
def mock_git_repo() -> Generator[mock.Mock, None, None]:
    """Fixture providing a mocked GitPython Repo instance."""
    with mock.patch("gitlabber.git.git") as mock_git:
        mock_repo_instance = mock.Mock()
        mock_git.Repo.return_value = mock_repo_instance
        mock_git.Repo.clone_from.return_value = mock_repo_instance
        yield mock_git


@pytest.fixture
def mock_gitlab_tree() -> Generator[mock.Mock, None, None]:
    """Fixture providing a mocked GitlabTree instance."""
    with mock.patch("gitlabber.cli.GitlabTree") as mock_tree:
        mock_instance = mock_tree.return_value
        mock_instance.is_empty.return_value = False
        mock_instance.api_concurrency = 5
        mock_instance.api_rate_limit = None
        yield mock_tree


@pytest.fixture
def mock_gitlabber_settings() -> Generator[mock.Mock, None, None]:
    """Fixture providing a mocked GitlabberSettings instance."""
    with mock.patch("gitlabber.cli.GitlabberSettings") as mock_settings:
        mock_instance = mock.Mock(spec=GitlabberSettings)
        mock_instance.token = None
        mock_instance.url = None
        mock_instance.method = None
        mock_instance.naming = None
        mock_instance.includes = None
        mock_instance.excludes = None
        mock_instance.concurrency = None
        mock_instance.api_concurrency = None
        mock_instance.api_rate_limit = None
        mock_settings.return_value = mock_instance
        yield mock_settings


@pytest.fixture
def default_settings() -> dict:
    """Fixture providing default settings for testing."""
    return {
        "token": TEST_TOKEN,
        "url": TEST_URL,
        "method": CloneMethod.SSH,
        "naming": "name",
        "includes": None,
        "excludes": None,
        "concurrency": 1,
        "hide_token": True,
    }


@pytest.fixture
def tmp_git_repo(tmp_path) -> Generator[str, None, None]:
    """Fixture providing a temporary directory that can be used as a git repo."""
    yield str(tmp_path)

