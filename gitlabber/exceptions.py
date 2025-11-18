"""Custom exceptions for gitlabber."""


class GitlabberError(Exception):
    """Base exception for gitlabber."""
    pass


class GitlabberConfigError(GitlabberError):
    """Configuration errors."""
    pass


class GitlabberAPIError(GitlabberError):
    """GitLab API errors."""
    pass


class GitlabberGitError(GitlabberError):
    """Git operation errors."""
    pass


class GitlabberAuthenticationError(GitlabberAPIError):
    """Authentication errors."""
    pass


class GitlabberTreeError(GitlabberError):
    """Tree-related errors."""
    pass

