"""Tests for CLI using improved mocking patterns."""
from typing import Optional
import pytest
from typer.testing import CliRunner
from gitlabber import cli
from gitlabber import __version__ as VERSION
from gitlabber.format import PrintFormat
from tests.test_helpers import TestConfigBuilder

runner = CliRunner()


def _invoke(args: list[str], env: Optional[dict[str, str]] = None):
    """Helper to invoke CLI with given arguments."""
    # Mocks handle environment isolation, so we just pass through
    return runner.invoke(cli.app, args, env=env)


@pytest.mark.skip(reason="CLI tests need environment isolation fixes for CI")
def test_version_option():
    result = _invoke(["--version"])
    assert result.exit_code == 0
    assert VERSION in result.stdout


@pytest.mark.skip(reason="CLI tests need environment isolation fixes for CI")
def test_missing_token_error(mock_gitlab_tree, mock_gitlabber_settings):
    """Test error handling when token is missing."""
    mock_gitlabber_settings.return_value = TestConfigBuilder.create_settings(url="https://example.com")
    result = _invoke(["--print"])
    assert result.exit_code == 1
    assert "Please specify a valid token" in (
        result.stdout or result.stderr or ""
    )
    mock_gitlab_tree.assert_not_called()


@pytest.mark.skip(reason="CLI tests need environment isolation fixes for CI")
def test_missing_url_error(mock_gitlab_tree, mock_gitlabber_settings):
    """Test error handling when URL is missing."""
    mock_gitlabber_settings.return_value = TestConfigBuilder.create_settings(token="token")
    result = _invoke(["--print"])
    assert result.exit_code == 1
    assert "Please specify a valid gitlab base url" in (
        result.stdout or result.stderr or ""
    )
    mock_gitlab_tree.assert_not_called()


@pytest.mark.skip(reason="CLI tests need environment isolation fixes for CI")
def test_missing_dest_error(mock_gitlab_tree, mock_gitlabber_settings):
    """Test error handling when destination is missing."""
    mock_gitlabber_settings.return_value = TestConfigBuilder.create_settings(
        token="token", url="https://example.com"
    )
    result = _invoke([])
    assert result.exit_code == 1
    assert "Please specify a destination" in (
        result.stdout or result.stderr or ""
    )
    mock_gitlab_tree.assert_not_called()


@pytest.mark.skip(reason="CLI tests need environment isolation fixes for CI")
def test_print_tree(mock_gitlab_tree, mock_gitlabber_settings):
    """Test printing tree structure."""
    mock_gitlabber_settings.return_value = TestConfigBuilder.create_settings()
    mock_gitlab_tree.return_value.is_empty.return_value = False
    result = _invoke(["-t", "token", "-u", "https://example.com", "--print"])
    assert result.exit_code == 0
    mock_gitlab_tree.return_value.print_tree.assert_called_once_with(PrintFormat.TREE)


@pytest.mark.skip(reason="CLI tests need environment isolation fixes for CI")
def test_sync_tree(mock_gitlab_tree, mock_gitlabber_settings):
    """Test syncing tree to destination."""
    mock_gitlabber_settings.return_value = TestConfigBuilder.create_settings()
    mock_gitlab_tree.return_value.is_empty.return_value = False
    result = _invoke(
        ["-t", "token", "-u", "https://example.com", "/tmp/gitlabber"]
    )
    assert result.exit_code == 0
    mock_gitlab_tree.return_value.sync_tree.assert_called_once_with("/tmp/gitlabber")


def test_convert_archived():
    """Test _convert_archived function."""
    from gitlabber.cli import _convert_archived
    from gitlabber.archive import ArchivedResults
    
    assert _convert_archived("include") == ArchivedResults.INCLUDE
    assert _convert_archived("exclude") == ArchivedResults.EXCLUDE
    assert _convert_archived("only") == ArchivedResults.ONLY
    assert _convert_archived("INCLUDE") == ArchivedResults.INCLUDE  # Case insensitive
    assert _convert_archived("ExClUdE") == ArchivedResults.EXCLUDE  # Case insensitive


def test_convert_archived_invalid():
    """Test _convert_archived with invalid value."""
    from gitlabber.cli import _convert_archived
    from typer import BadParameter
    
    with pytest.raises(BadParameter):
        _convert_archived("invalid")


def test_cli_main_function():
    """Test main() function calls app()."""
    from unittest import mock
    from gitlabber.cli import main
    
    with mock.patch('gitlabber.cli.app') as mock_app:
        main()
        mock_app.assert_called_once()
