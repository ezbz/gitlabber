from unittest import mock

from gitlabber.method import CloneMethod
from gitlabber.url_builder import build_project_url, select_project_url


def test_select_project_url_http():
    url = select_project_url(
        http_url="https://example.com/http.git",
        ssh_url="git@example.com:ssh.git",
        method=CloneMethod.HTTP,
    )
    assert url == "https://example.com/http.git"


def test_select_project_url_ssh():
    url = select_project_url(
        http_url="https://example.com/http.git",
        ssh_url="git@example.com:ssh.git",
        method=CloneMethod.SSH,
    )
    assert url == "git@example.com:ssh.git"


def test_build_project_url_with_token_injection():
    logger = mock.Mock()
    url = build_project_url(
        http_url="https://example.com/group/project.git",
        ssh_url="git@example.com:group/project.git",
        method=CloneMethod.HTTP,
        token="secret",
        hide_token=False,
        logger=logger,
    )
    assert url == "https://gitlab-token:secret@example.com/group/project.git"
    logger.debug.assert_called_with(
        "Generated URL: %s", "https://gitlab-token:secret@example.com/group/project.git"
    )


def test_build_project_url_hide_token():
    logger = mock.Mock()
    base_url = "https://example.com/group/project.git"
    url = build_project_url(
        http_url=base_url,
        ssh_url="git@example.com:group/project.git",
        method=CloneMethod.HTTP,
        token="secret",
        hide_token=True,
        logger=logger,
    )
    assert url == base_url
    logger.debug.assert_called_with("Hiding token from project url: %s", base_url)


def test_build_project_url_ssh_ignores_token():
    logger = mock.Mock()
    ssh_url = "git@example.com:group/project.git"
    url = build_project_url(
        http_url="https://example.com/group/project.git",
        ssh_url=ssh_url,
        method=CloneMethod.SSH,
        token="secret",
        hide_token=False,
        logger=logger,
    )
    assert url == ssh_url
    logger.debug.assert_not_called()


def test_build_project_url_no_token():
    """Test build_project_url when token is None."""
    url = build_project_url(
        http_url="https://example.com/group/project.git",
        ssh_url="git@example.com:group/project.git",
        method=CloneMethod.HTTP,
        token=None,
        hide_token=False,
        logger=None,
    )
    assert url == "https://example.com/group/project.git"


def test_build_project_url_no_logger():
    """Test build_project_url when logger is None (uses default logger)."""
    url = build_project_url(
        http_url="https://example.com/group/project.git",
        ssh_url="git@example.com:group/project.git",
        method=CloneMethod.HTTP,
        token="secret",
        hide_token=False,
        logger=None,
    )
    assert url == "https://gitlab-token:secret@example.com/group/project.git"

