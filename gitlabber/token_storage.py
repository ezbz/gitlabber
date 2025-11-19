"""Secure token storage using OS keyring.

This module provides a simple interface for storing and retrieving GitLab
tokens securely using the OS-native keyring. If keyring is not available,
the storage gracefully degrades and returns None.
"""

from typing import Optional


class TokenStorageError(Exception):
    """Exception raised for token storage errors."""
    pass


class TokenStorage:
    """Simple token storage using OS keyring.
    
    This class provides secure storage for GitLab tokens using the OS-native
    keyring (Keychain on macOS, Secret Service on Linux, Credential Manager
    on Windows). If the keyring library is not available, all operations
    gracefully fail and return None.
    
    Attributes:
        SERVICE_NAME: Service name used in keyring (identifies gitlabber)
    """
    
    SERVICE_NAME = "gitlabber"
    
    def __init__(self):
        """Initialize token storage.
        
        Attempts to import the keyring library. If unavailable, storage
        operations will return None or raise TokenStorageError.
        """
        self._keyring = None
        self._try_import_keyring()
    
    def _try_import_keyring(self) -> None:
        """Try to import keyring, fail silently if unavailable."""
        try:
            import keyring
            self._keyring = keyring
        except ImportError:
            self._keyring = None
    
    def is_available(self) -> bool:
        """Check if keyring storage is available.
        
        Returns:
            True if keyring is available, False otherwise
        """
        return self._keyring is not None
    
    def store(self, url: str, token: str) -> None:
        """Store token for a GitLab URL.
        
        Args:
            url: GitLab instance URL (e.g., https://gitlab.com)
            token: GitLab personal access token
            
        Raises:
            TokenStorageError: If keyring is not available or storage fails
        """
        if not self.is_available():
            raise TokenStorageError(
                "Keyring not available. Install with: pip install keyring"
            )
        try:
            self._keyring.set_password(self.SERVICE_NAME, url, token)
        except Exception as e:
            raise TokenStorageError(f"Failed to store token: {str(e)}") from e
    
    def retrieve(self, url: str) -> Optional[str]:
        """Retrieve token for a GitLab URL.
        
        Args:
            url: GitLab instance URL
            
        Returns:
            Token if found and keyring is available, None otherwise
        """
        if not self.is_available():
            return None
        try:
            return self._keyring.get_password(self.SERVICE_NAME, url)
        except Exception:
            # Keyring errors (permissions, etc.) - return None gracefully
            return None
    
    def delete(self, url: str) -> None:
        """Delete stored token for a GitLab URL.
        
        Args:
            url: GitLab instance URL
        """
        if not self.is_available():
            return
        try:
            self._keyring.delete_password(self.SERVICE_NAME, url)
        except Exception:
            # Ignore if not found or other errors
            pass
    
    def list_stored_urls(self) -> list[str]:
        """List all URLs with stored tokens.
        
        Note: Most keyring backends don't support listing credentials.
        This method returns an empty list for compatibility.
        
        Returns:
            List of URLs (empty for keyring backends)
        """
        # Keyring doesn't support listing credentials
        # This is a limitation of most keyring backends
        return []

