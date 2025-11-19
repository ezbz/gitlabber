"""Tests for configuration classes."""

from gitlabber.config import GitlabberSettings, GitlabberConfig
from gitlabber.method import CloneMethod


def test_settings_split_csv_none():
    """Test _split_csv with None value."""
    settings = GitlabberSettings(token="test", url="https://example.com")
    assert settings.includes is None
    assert settings.excludes is None


def test_settings_split_csv_empty_string():
    """Test _split_csv with empty string."""
    settings = GitlabberSettings(
        token="test",
        url="https://example.com",
        includes="",
        excludes=""
    )
    assert settings.includes is None
    assert settings.excludes is None


def test_settings_split_csv_list():
    """Test _split_csv with list value."""
    # GitlabberSettings uses environment variables, so we need to set them
    import os
    os.environ['GITLABBER_INCLUDE'] = "item1,item2"
    try:
        settings = GitlabberSettings(
            token="test",
            url="https://example.com"
        )
        assert settings.includes == ["item1", "item2"]
    finally:
        os.environ.pop('GITLABBER_INCLUDE', None)


def test_config_ensure_str_list_none():
    """Test _ensure_str_list with None value."""
    config = GitlabberConfig(
        url="https://example.com",
        token="test",
        method=CloneMethod.SSH,
        includes=None,
        excludes=None
    )
    assert config.includes is None
    assert config.excludes is None


def test_config_ensure_str_list_empty_string():
    """Test _ensure_str_list with empty string."""
    config = GitlabberConfig(
        url="https://example.com",
        token="test",
        method=CloneMethod.SSH,
        includes="",
        excludes=""
    )
    assert config.includes is None
    assert config.excludes is None


def test_config_ensure_str_list_string():
    """Test _ensure_str_list with string value."""
    config = GitlabberConfig(
        url="https://example.com",
        token="test",
        method=CloneMethod.SSH,
        includes="pattern1",
        excludes="pattern2"
    )
    assert config.includes == ["pattern1"]
    assert config.excludes == ["pattern2"]


def test_config_ensure_str_list_list():
    """Test _ensure_str_list with list value."""
    config = GitlabberConfig(
        url="https://example.com",
        token="test",
        method=CloneMethod.SSH,
        includes=["pattern1", "pattern2"],
        excludes=["pattern3"]
    )
    assert config.includes == ["pattern1", "pattern2"]
    assert config.excludes == ["pattern3"]

