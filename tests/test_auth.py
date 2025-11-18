"""Tests for authentication providers."""

import pytest
from unittest import mock
from gitlabber.auth import AuthProvider, TokenAuthProvider, NoAuthProvider
from gitlab.exceptions import GitlabAuthenticationError


def test_auth_provider_abstract():
    """Test that AuthProvider is abstract and cannot be instantiated."""
    with pytest.raises(TypeError):
        AuthProvider()


def test_token_auth_provider_init():
    """Test TokenAuthProvider initialization."""
    provider = TokenAuthProvider("test-token")
    assert provider.token == "test-token"


def test_token_auth_provider_authenticate():
    """Test TokenAuthProvider.authenticate() calls gitlab_client.auth()."""
    provider = TokenAuthProvider("test-token")
    mock_client = mock.Mock()
    
    provider.authenticate(mock_client)
    
    mock_client.auth.assert_called_once()


def test_token_auth_provider_authenticate_error():
    """Test TokenAuthProvider.authenticate() raises GitlabAuthenticationError on failure."""
    provider = TokenAuthProvider("test-token")
    mock_client = mock.Mock()
    mock_client.auth.side_effect = GitlabAuthenticationError("Invalid token")
    
    with pytest.raises(GitlabAuthenticationError):
        provider.authenticate(mock_client)


def test_no_auth_provider_authenticate():
    """Test NoAuthProvider.authenticate() does nothing."""
    provider = NoAuthProvider()
    mock_client = mock.Mock()
    
    # Should not raise any exception
    provider.authenticate(mock_client)
    
    # Client should not be called
    mock_client.assert_not_called()

