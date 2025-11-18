"""Custom exceptions for gitlabber with actionable error messages."""

from typing import Optional


class GitlabberError(Exception):
    """Base exception for gitlabber with support for actionable suggestions."""
    
    def __init__(self, message: str, suggestion: Optional[str] = None):
        """Initialize error with message and optional suggestion.
        
        Args:
            message: Error message describing what went wrong
            suggestion: Optional actionable suggestion for the user
        """
        self.message = message
        self.suggestion = suggestion
        if suggestion:
            super().__init__(f"{message}\n\n💡 Suggestion: {suggestion}")
        else:
            super().__init__(message)


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


def format_error_with_suggestion(
    error_type: str,
    message: str,
    context: Optional[dict] = None
) -> tuple[str, Optional[str]]:
    """Format error message with actionable suggestion.
    
    Args:
        error_type: Type of error (e.g., 'git_clone', 'api_auth', 'permission')
        message: Base error message
        context: Optional context dictionary with additional info
        
    Returns:
        Tuple of (formatted_message, suggestion)
    """
    context = context or {}
    suggestions = {
        'git_clone_ssh': (
            "If using SSH, ensure your SSH key is added to GitLab. "
            "See: https://docs.gitlab.com/ee/user/ssh.html\n"
            "Alternatively, try using HTTP method: `gitlabber -m http ...`"
        ),
        'git_clone_permission': (
            "Check that your GitLab token has 'read_repository' scope.\n"
            "Verify you have access to the project in GitLab web interface."
        ),
        'git_clone_network': (
            "Check your network connection and GitLab instance availability.\n"
            "For GitLab.com, ensure you're not behind a restrictive firewall."
        ),
        'git_pull_branch': (
            "The local branch may no longer exist on the remote.\n"
            "Try using `--use-fetch` flag: `gitlabber --use-fetch ...`\n"
            "Or manually check out a different branch in the repository."
        ),
        'api_auth': (
            "Verify your GitLab token is valid and has required scopes:\n"
            "- 'read_api' or 'api' (for GitLab <12.0)\n"
            "- 'read_repository'\n"
            "Generate a new token at: https://gitlab.com/-/profile/personal_access_tokens"
        ),
        'api_permission': (
            "You may not have permission to access this resource.\n"
            "Check your GitLab permissions or contact your GitLab administrator.\n"
            "Verify the group/project exists and you're a member."
        ),
        'api_rate_limit': (
            "GitLab API rate limit exceeded. Options:\n"
            "- Wait and retry later\n"
            "- Use `--api-rate-limit` to set a lower limit\n"
            "- Reduce `--api-concurrency` value"
        ),
        'api_404': (
            "Resource not found. Possible causes:\n"
            "- Project/group was deleted or moved\n"
            "- You don't have access to this resource\n"
            "- URL or group name is incorrect\n"
            "Verify the resource exists in GitLab web interface."
        ),
        'api_503': (
            "GitLab service unavailable. Ensure you're using the correct base URL:\n"
            "- For GitLab.com: https://gitlab.com\n"
            "- For self-hosted: your instance base URL (e.g., https://gitlab.example.com)\n"
            "Do not include paths like /some/nested/path"
        ),
        'config_missing': (
            "Required configuration is missing. Provide:\n"
            "- GitLab URL via `-u/--url` or `GITLAB_URL` environment variable\n"
            "- Access token via `-t/--token` or `GITLAB_TOKEN` environment variable"
        ),
        'tree_empty': (
            "No projects found matching your criteria. Try:\n"
            "- Check your include/exclude patterns with `-p` flag\n"
            "- Use `--verbose` for debugging\n"
            "- Verify you have access to groups/projects\n"
            "- Use `--group-search` to filter at API level for large instances"
        ),
    }
    
    suggestion = suggestions.get(error_type)
    if not suggestion and context:
        # Generate generic suggestion based on context
        if 'url' in context:
            suggestion = "Verify the GitLab URL is correct and accessible."
        elif 'token' in context:
            suggestion = "Verify your access token is valid and has required permissions."
    
    return message, suggestion

