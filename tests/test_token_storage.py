"""Tests for token storage functionality."""

import pytest
from unittest import mock
from gitlabber.token_storage import TokenStorage, TokenStorageError


class TestTokenStorage:
    """Test cases for TokenStorage class."""
    
    def test_init_without_keyring(self):
        """Test initialization when keyring is not available."""
        # Create storage and manually set keyring to None to simulate unavailable state
        storage = TokenStorage()
        storage._keyring = None
        assert not storage.is_available()
    
    def test_init_with_keyring(self):
        """Test initialization when keyring is available."""
        # Just verify that if keyring is set, is_available returns True
        storage = TokenStorage()
        # If keyring is actually available, test that
        if storage._keyring is not None:
            assert storage.is_available()
        else:
            # If not available, manually set it to test the logic
            storage._keyring = mock.MagicMock()
            assert storage.is_available()
    
    def test_store_without_keyring(self):
        """Test storing token when keyring is not available."""
        storage = TokenStorage()
        # Mock is_available to return False
        storage._keyring = None
        
        with pytest.raises(TokenStorageError, match="Keyring not available"):
            storage.store("https://gitlab.com", "test-token")
    
    def test_store_with_keyring(self):
        """Test storing token when keyring is available."""
        mock_keyring = mock.MagicMock()
        storage = TokenStorage()
        storage._keyring = mock_keyring
        storage.store("https://gitlab.com", "test-token")
        mock_keyring.set_password.assert_called_once_with(
            "gitlabber", "https://gitlab.com", "test-token"
        )
    
    def test_store_error_handling(self):
        """Test error handling when storing fails."""
        mock_keyring = mock.MagicMock()
        mock_keyring.set_password.side_effect = Exception("Storage error")
        storage = TokenStorage()
        storage._keyring = mock_keyring
        with pytest.raises(TokenStorageError, match="Failed to store token"):
            storage.store("https://gitlab.com", "test-token")
    
    def test_retrieve_without_keyring(self):
        """Test retrieving token when keyring is not available."""
        storage = TokenStorage()
        storage._keyring = None
        assert storage.retrieve("https://gitlab.com") is None
    
    def test_retrieve_with_keyring(self):
        """Test retrieving token when keyring is available."""
        mock_keyring = mock.MagicMock()
        mock_keyring.get_password.return_value = "stored-token"
        storage = TokenStorage()
        storage._keyring = mock_keyring
        result = storage.retrieve("https://gitlab.com")
        assert result == "stored-token"
        mock_keyring.get_password.assert_called_once_with(
            "gitlabber", "https://gitlab.com"
        )
    
    def test_retrieve_not_found(self):
        """Test retrieving token that doesn't exist."""
        mock_keyring = mock.MagicMock()
        mock_keyring.get_password.return_value = None
        storage = TokenStorage()
        storage._keyring = mock_keyring
        result = storage.retrieve("https://gitlab.com")
        assert result is None
    
    def test_retrieve_error_handling(self):
        """Test error handling when retrieval fails."""
        mock_keyring = mock.MagicMock()
        mock_keyring.get_password.side_effect = Exception("Retrieval error")
        storage = TokenStorage()
        storage._keyring = mock_keyring
        # Should return None gracefully on error
        result = storage.retrieve("https://gitlab.com")
        assert result is None
    
    def test_delete_without_keyring(self):
        """Test deleting token when keyring is not available."""
        storage = TokenStorage()
        storage._keyring = None
        # Should not raise
        storage.delete("https://gitlab.com")
    
    def test_delete_with_keyring(self):
        """Test deleting token when keyring is available."""
        mock_keyring = mock.MagicMock()
        storage = TokenStorage()
        storage._keyring = mock_keyring
        storage.delete("https://gitlab.com")
        mock_keyring.delete_password.assert_called_once_with(
            "gitlabber", "https://gitlab.com"
        )
    
    def test_delete_error_handling(self):
        """Test error handling when deletion fails."""
        mock_keyring = mock.MagicMock()
        mock_keyring.delete_password.side_effect = Exception("Delete error")
        storage = TokenStorage()
        storage._keyring = mock_keyring
        # Should not raise, just ignore
        storage.delete("https://gitlab.com")
    
    def test_list_stored_urls(self):
        """Test listing stored URLs (returns empty for keyring)."""
        storage = TokenStorage()
        # Keyring doesn't support listing, should return empty list
        assert storage.list_stored_urls() == []

