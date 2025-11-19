"""Tests for CLI token storage functionality."""

import os
import pytest
from unittest import mock
from typer.testing import CliRunner
from gitlabber import cli
from gitlabber.token_storage import TokenStorageError

runner = CliRunner()

# Skip CLI tests in CI environment (GitHub Actions)
skip_in_ci = pytest.mark.skipif(
    os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true",
    reason="CLI tests need environment isolation fixes for CI"
)


def test_resolve_token_from_storage(mock_gitlab_tree, mock_gitlabber_settings):
    """Test that _resolve_token retrieves token from secure storage."""
    from gitlabber.cli import _resolve_token
    from gitlabber.config import GitlabberSettings
    
    # Create settings with no token
    settings = GitlabberSettings()
    settings.token = None
    
    # Mock TokenStorage to return a stored token
    with mock.patch('gitlabber.cli.TokenStorage') as mock_storage_class:
        mock_storage = mock.MagicMock()
        mock_storage_class.return_value = mock_storage
        mock_storage.is_available.return_value = True
        mock_storage.retrieve.return_value = "stored-token-123"
        
        # Should return stored token
        result = _resolve_token(None, "https://gitlab.com", settings)
        assert result == "stored-token-123"
        mock_storage.retrieve.assert_called_once_with("https://gitlab.com")


def test_resolve_token_priority_cli_over_storage(mock_gitlab_tree, mock_gitlabber_settings):
    """Test that CLI token takes priority over stored token."""
    from gitlabber.cli import _resolve_token
    from gitlabber.config import GitlabberSettings
    
    settings = GitlabberSettings()
    settings.token = None
    
    with mock.patch('gitlabber.cli.TokenStorage') as mock_storage_class:
        mock_storage = mock.MagicMock()
        mock_storage_class.return_value = mock_storage
        mock_storage.is_available.return_value = True
        mock_storage.retrieve.return_value = "stored-token"
        
        # CLI token should be used, storage should not be checked
        result = _resolve_token("cli-token", "https://gitlab.com", settings)
        assert result == "cli-token"
        mock_storage.retrieve.assert_not_called()


@skip_in_ci
def test_store_token_success(mock_gitlabber_settings):
    """Test successful token storage via CLI."""
    mock_gitlabber_settings.return_value.token = None
    mock_gitlabber_settings.return_value.url = "https://gitlab.com"
    
    with mock.patch('gitlabber.cli.TokenStorage') as mock_storage_class:
        mock_storage = mock.MagicMock()
        mock_storage_class.return_value = mock_storage
        mock_storage.is_available.return_value = True
        
        result = runner.invoke(
            cli.app,
            ["--store-token", "-u", "https://gitlab.com", "-t", "test-token"],
            input="",  # No prompt input needed since token provided
        )
        
        assert result.exit_code == 0
        assert "Token stored securely" in result.stdout or "Token stored securely" in result.stderr
        mock_storage.store.assert_called_once_with("https://gitlab.com", "test-token")


@skip_in_ci
def test_store_token_prompt(mock_gitlabber_settings):
    """Test token storage with prompt when token not provided."""
    mock_gitlabber_settings.return_value.token = None
    mock_gitlabber_settings.return_value.url = "https://gitlab.com"
    
    with mock.patch('gitlabber.cli.TokenStorage') as mock_storage_class, \
         mock.patch('gitlabber.cli.typer.prompt', return_value="prompted-token"):
        mock_storage = mock.MagicMock()
        mock_storage_class.return_value = mock_storage
        mock_storage.is_available.return_value = True
        
        result = runner.invoke(
            cli.app,
            ["--store-token", "-u", "https://gitlab.com"],
        )
        
        assert result.exit_code == 0
        assert "Token stored securely" in result.stdout or "Token stored securely" in result.stderr
        mock_storage.store.assert_called_once_with("https://gitlab.com", "prompted-token")


@skip_in_ci
def test_store_token_no_url(mock_gitlabber_settings):
    """Test token storage fails when URL is missing."""
    mock_gitlabber_settings.return_value.token = None
    mock_gitlabber_settings.return_value.url = None
    
    result = runner.invoke(cli.app, ["--store-token"])
    
    assert result.exit_code == 1
    assert "URL required for storing token" in result.stderr or "URL required for storing token" in result.stdout


@skip_in_ci
def test_store_token_keyring_unavailable(mock_gitlabber_settings):
    """Test token storage fails when keyring is unavailable."""
    mock_gitlabber_settings.return_value.token = None
    mock_gitlabber_settings.return_value.url = "https://gitlab.com"
    
    with mock.patch('gitlabber.cli.TokenStorage') as mock_storage_class:
        mock_storage = mock.MagicMock()
        mock_storage_class.return_value = mock_storage
        mock_storage.is_available.return_value = False
        
        result = runner.invoke(
            cli.app,
            ["--store-token", "-u", "https://gitlab.com", "-t", "test-token"],
        )
        
        assert result.exit_code == 1
        assert "keyring not available" in result.stderr or "keyring not available" in result.stdout


@skip_in_ci
def test_store_token_storage_error(mock_gitlabber_settings):
    """Test token storage handles TokenStorageError."""
    mock_gitlabber_settings.return_value.token = None
    mock_gitlabber_settings.return_value.url = "https://gitlab.com"
    
    with mock.patch('gitlabber.cli.TokenStorage') as mock_storage_class:
        mock_storage = mock.MagicMock()
        mock_storage_class.return_value = mock_storage
        mock_storage.is_available.return_value = True
        mock_storage.store.side_effect = TokenStorageError("Storage failed")
        
        result = runner.invoke(
            cli.app,
            ["--store-token", "-u", "https://gitlab.com", "-t", "test-token"],
        )
        
        assert result.exit_code == 1
        assert "Storage failed" in result.stderr or "Storage failed" in result.stdout


def test_validate_positive_int_error():
    """Test _validate_positive_int raises error for invalid values."""
    from gitlabber.cli import _validate_positive_int
    from typer import BadParameter
    
    with pytest.raises(BadParameter, match="must be a positive integer"):
        _validate_positive_int(0)
    
    with pytest.raises(BadParameter, match="must be a positive integer"):
        _validate_positive_int(-1)


def test_validate_positive_int_success():
    """Test _validate_positive_int returns value for valid inputs."""
    from gitlabber.cli import _validate_positive_int
    
    assert _validate_positive_int(1) == 1
    assert _validate_positive_int(5) == 5
    assert _validate_positive_int(100) == 100


def test_split_csv_none():
    """Test _split_csv with None input."""
    from gitlabber.cli import _split_csv
    
    assert _split_csv(None) is None


def test_split_csv_empty():
    """Test _split_csv with empty string."""
    from gitlabber.cli import _split_csv
    
    assert _split_csv("") is None
    assert _split_csv("   ") is None


def test_split_csv_with_values():
    """Test _split_csv with actual values."""
    from gitlabber.cli import _split_csv
    
    result = _split_csv("a,b,c")
    assert result == ["a", "b", "c"]
    
    result = _split_csv("  a  ,  b  ,  c  ")
    assert result == ["a", "b", "c"]
    
    # Empty after stripping should return None
    result = _split_csv("  ,  ,  ")
    assert result is None


def test_config_logging_verbose_print_mode():
    """Test config_logging with verbose and print_mode."""
    from gitlabber.cli import config_logging
    import logging
    
    # Reset logging
    logging.root.handlers = []
    logging.root.setLevel(logging.WARNING)
    
    config_logging(verbose=True, print_mode=True)
    
    # Should set level to ERROR when print_mode is True
    assert logging.root.level == logging.ERROR
    assert len(logging.root.handlers) > 0


def test_config_logging_verbose_no_print_mode():
    """Test config_logging with verbose but no print_mode."""
    from gitlabber.cli import config_logging
    import logging
    
    # Reset logging
    logging.root.handlers = []
    logging.root.setLevel(logging.WARNING)
    
    config_logging(verbose=True, print_mode=False)
    
    # Should set level to DEBUG when print_mode is False
    assert logging.root.level == logging.DEBUG
    assert len(logging.root.handlers) > 0

