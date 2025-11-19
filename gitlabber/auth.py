"""Authentication providers for GitLab API access.

This module defines the authentication interface and implementations
for authenticating with GitLab instances. It supports token-based
authentication and provides a no-op provider for testing.
"""

from abc import ABC, abstractmethod
from gitlab import Gitlab

class AuthProvider(ABC):
    """Interface for GitLab authentication providers."""
    
    @abstractmethod
    def authenticate(self, gitlab_client: Gitlab) -> None:
        """Authenticate the GitLab client.
        
        Args:
            gitlab_client: The GitLab client to authenticate
            
        Raises:
            GitlabAuthenticationError: If authentication fails
        """
        pass

class TokenAuthProvider(AuthProvider):
    """Authentication provider using a personal access token."""
    
    def __init__(self, token: str) -> None:
        """Initialize with a personal access token.
        
        Args:
            token: GitLab personal access token
        """
        self.token = token
        
    def authenticate(self, gitlab_client: Gitlab) -> None:
        """Authenticate using the personal access token.
        
        Args:
            gitlab_client: The GitLab client to authenticate
            
        Raises:
            GitlabAuthenticationError: If authentication fails
        """
        gitlab_client.auth()

class NoAuthProvider(AuthProvider):
    """Authentication provider that performs no authentication.
    
    This is useful for testing or when authentication is handled externally.
    """
    
    def authenticate(self, gitlab_client: Gitlab) -> None:
        """Perform no authentication.
        
        Args:
            gitlab_client: The GitLab client (not used)
        """
        pass 