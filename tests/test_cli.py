from typing import Optional

from typer.testing import CliRunner
from gitlabber import cli
from gitlabber import __version__ as VERSION
from gitlabber.format import PrintFormat
from unittest import mock

runner = CliRunner()


def _invoke(args: list[str], env: Optional[dict[str, str]] = None):
    return runner.invoke(cli.app, args, env=env)


def test_version_option():
    result = _invoke(["--version"])
    assert result.exit_code == 0
    assert VERSION in result.stdout


@mock.patch("gitlabber.cli.GitlabTree")
def test_missing_token_error(mock_tree: mock.Mock):
    result = _invoke(
        ["-u", "https://example.com", "--print"],
        env={"GITLAB_TOKEN": ""},
    )
    assert result.exit_code == 1
    assert "Please specify a valid token" in (
        result.stdout or result.stderr or ""
    )
    mock_tree.assert_not_called()


@mock.patch("gitlabber.cli.GitlabTree")
def test_missing_url_error(mock_tree: mock.Mock):
    result = _invoke(["-t", "token", "--print"])
    assert result.exit_code == 1
    assert "Please specify a valid gitlab base url" in (
        result.stdout or result.stderr or ""
    )
    mock_tree.assert_not_called()


@mock.patch("gitlabber.cli.GitlabTree")
def test_missing_dest_error(mock_tree: mock.Mock):
    result = _invoke(["-t", "token", "-u", "https://example.com"])
    assert result.exit_code == 1
    assert "Please specify a destination" in (
        result.stdout or result.stderr or ""
    )
    mock_tree.assert_not_called()


@mock.patch("gitlabber.cli.GitlabTree")
def test_print_tree(mock_tree: mock.Mock):
    mock_tree.return_value.is_empty.return_value = False
    result = _invoke(["-t", "token", "-u", "https://example.com", "--print"])
    assert result.exit_code == 0
    mock_tree.return_value.print_tree.assert_called_once_with(PrintFormat.TREE)


@mock.patch("gitlabber.cli.GitlabTree")
def test_sync_tree(mock_tree: mock.Mock):
    mock_tree.return_value.is_empty.return_value = False
    result = _invoke(
        ["-t", "token", "-u", "https://example.com", "/tmp/gitlabber"]
    )
    assert result.exit_code == 0
    mock_tree.return_value.sync_tree.assert_called_once_with("/tmp/gitlabber")
