"""Tests for exception handling and error formatting."""

from gitlabber.exceptions import (
    GitlabberError,
    GitlabberConfigError,
    GitlabberAPIError,
    GitlabberGitError,
    GitlabberAuthenticationError,
    GitlabberTreeError,
    format_error_with_suggestion,
)


def test_gitlabber_error_with_suggestion():
    """Test GitlabberError with suggestion."""
    error = GitlabberError("Test error", "Test suggestion")
    assert error.message == "Test error"
    assert error.suggestion == "Test suggestion"
    assert "Test error" in str(error)
    assert "Test suggestion" in str(error)


def test_gitlabber_error_without_suggestion():
    """Test GitlabberError without suggestion."""
    error = GitlabberError("Test error")
    assert error.message == "Test error"
    assert error.suggestion is None
    assert "Test error" in str(error)
    assert "Suggestion" not in str(error)


def test_error_hierarchy():
    """Test exception hierarchy."""
    assert issubclass(GitlabberConfigError, GitlabberError)
    assert issubclass(GitlabberAPIError, GitlabberError)
    assert issubclass(GitlabberGitError, GitlabberError)
    assert issubclass(GitlabberAuthenticationError, GitlabberAPIError)
    assert issubclass(GitlabberTreeError, GitlabberError)


def test_format_error_with_suggestion_known_type():
    """Test format_error_with_suggestion with known error type."""
    message, suggestion = format_error_with_suggestion(
        'api_auth',
        "Authentication failed"
    )
    assert message == "Authentication failed"
    assert suggestion is not None
    assert "token" in suggestion.lower() or "api" in suggestion.lower()


def test_format_error_with_suggestion_unknown_type_with_url_context():
    """Test format_error_with_suggestion with unknown type but URL context."""
    message, suggestion = format_error_with_suggestion(
        'unknown_error',
        "Something went wrong",
        context={'url': 'https://gitlab.com'}
    )
    assert message == "Something went wrong"
    assert suggestion == "Verify the GitLab URL is correct and accessible."


def test_format_error_with_suggestion_unknown_type_with_token_context():
    """Test format_error_with_suggestion with unknown type but token context."""
    message, suggestion = format_error_with_suggestion(
        'unknown_error',
        "Something went wrong",
        context={'token': 'some-token'}
    )
    assert message == "Something went wrong"
    assert suggestion == "Verify your access token is valid and has required permissions."


def test_format_error_with_suggestion_unknown_type_no_context():
    """Test format_error_with_suggestion with unknown type and no context."""
    message, suggestion = format_error_with_suggestion(
        'unknown_error',
        "Something went wrong"
    )
    assert message == "Something went wrong"
    assert suggestion is None


def test_format_error_with_suggestion_unknown_type_empty_context():
    """Test format_error_with_suggestion with unknown type and empty context."""
    message, suggestion = format_error_with_suggestion(
        'unknown_error',
        "Something went wrong",
        context={}
    )
    assert message == "Something went wrong"
    assert suggestion is None

