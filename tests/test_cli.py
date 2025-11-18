from typing import Optional

from typer.testing import CliRunner
from gitlabber import cli
from gitlabber import __version__ as VERSION
from gitlabber.format import PrintFormat
from unittest import mock

runner = CliRunner()


def _invoke(args: list[str], env: Optional[dict[str, str]] = None):
    return runner.invoke(cli.app, args, env=env)


def _make_settings(**overrides):
    defaults = {
        "token": None,
        "url": None,
        "method": None,
        "naming": None,
        "includes": None,
        "excludes": None,
        "concurrency": None,
    }
    defaults.update(overrides)
    return mock.Mock(**defaults)


def test_version_option():
    result = _invoke(["--version"])
    assert result.exit_code == 0
    assert VERSION in result.stdout


@mock.patch("gitlabber.cli.GitlabTree")
@mock.patch("gitlabber.cli.GitlabberSettings")
def test_missing_token_error(mock_settings, mock_tree: mock.Mock):
    mock_settings.return_value = _make_settings(url="https://example.com")
    result = _invoke(["--print"])
    assert result.exit_code == 1
    assert "Please specify a valid token" in (
        result.stdout or result.stderr or ""
    )
    mock_tree.assert_not_called()


@mock.patch("gitlabber.cli.GitlabTree")
@mock.patch("gitlabber.cli.GitlabberSettings")
def test_missing_url_error(mock_settings, mock_tree: mock.Mock):
    mock_settings.return_value = _make_settings(token="token")
    result = _invoke(["--print"])
    assert result.exit_code == 1
    assert "Please specify a valid gitlab base url" in (
        result.stdout or result.stderr or ""
    )
    mock_tree.assert_not_called()


@mock.patch("gitlabber.cli.GitlabTree")
@mock.patch("gitlabber.cli.GitlabberSettings")
def test_missing_dest_error(mock_settings, mock_tree: mock.Mock):
    mock_settings.return_value = _make_settings(
        token="token", url="https://example.com"
    )
    result = _invoke([])
    assert result.exit_code == 1
    assert "Please specify a destination" in (
        result.stdout or result.stderr or ""
    )
    mock_tree.assert_not_called()


@mock.patch("gitlabber.cli.GitlabTree")
@mock.patch("gitlabber.cli.GitlabberSettings")
def test_print_tree(mock_settings, mock_tree: mock.Mock):
    mock_settings.return_value = _make_settings()
    mock_tree.return_value.is_empty.return_value = False
    result = _invoke(["-t", "token", "-u", "https://example.com", "--print"])
    assert result.exit_code == 0
    mock_tree.return_value.print_tree.assert_called_once_with(PrintFormat.TREE)


@mock.patch("gitlabber.cli.GitlabTree")
@mock.patch("gitlabber.cli.GitlabberSettings")
def test_sync_tree(mock_settings, mock_tree: mock.Mock):
    mock_settings.return_value = _make_settings()
    mock_tree.return_value.is_empty.return_value = False
    result = _invoke(
        ["-t", "token", "-u", "https://example.com", "/tmp/gitlabber"]
    )
    assert result.exit_code == 0
    mock_tree.return_value.sync_tree.assert_called_once_with("/tmp/gitlabber")
