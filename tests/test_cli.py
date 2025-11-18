from gitlabber import cli
from gitlabber import __version__ as VERSION
import tests.io_test_util as output_util
from typing import Any, Dict, cast
import pytest
from unittest import mock
from argparse import Namespace
from anytree import Node
from gitlabber.format import PrintFormat
from gitlabber.method import CloneMethod
from gitlabber.naming import FolderNaming
from gitlabber.archive import ArchivedResults


def exit():
    import sys
    sys.exit()


def test_args_version():
    args_mock = mock.Mock()
    args_mock.return_value = Node(type="test", name="test", version=True)
    cli.parse_args = args_mock

    with output_util.captured_output() as (out, err):
        with pytest.raises(SystemExit):
            cli.main()
            assert VERSION == out.getvalue()


def create_mock_args(overrides: Dict[str, Any] = None) -> mock.Mock:
    """Create a mock args object with default values that can be overridden"""
    base_args = {
        "type": "test",
        "name": "test",
        "version": None,
        "verbose": None,
        "include": "",
        "exclude": "",
        "url": "test_url",
        "token": "test_token",
        "method": CloneMethod.SSH,
        "naming": FolderNaming.NAME,
        "archived": ArchivedResults.INCLUDE,
        "file": None,
        "concurrency": 1,
        "recursive": False,
        "disable_progress": True,
        "print": True,
        "print_format": PrintFormat.TREE,
        "dest": ".",
        "include_shared": True,
        "use_fetch": None,
        "hide_token": None,
        "user_projects": None,
        "group_search": None,
        "git_options": None,
        "fail_fast": False
    }
    if overrides:
        base_args.update(overrides)
    args_mock = mock.Mock()
    args_mock.return_value = Node(**base_args)
    return args_mock


@mock.patch("gitlabber.cli.logging")
@mock.patch("gitlabber.cli.sys")
@mock.patch("gitlabber.cli.os")
@mock.patch("gitlabber.cli.log")
@mock.patch("gitlabber.cli.GitlabTree")
def test_args_logging(
    mock_tree: mock.Mock,
    mock_log: mock.Mock,
    mock_os: mock.Mock,
    mock_sys: mock.Mock,
    mock_logging: mock.Mock
) -> None:
    args_mock = create_mock_args({"verbose": True, "naming": FolderNaming.PATH, "fail_fast": True})
    cli.parse_args = args_mock

    mock_streamhandler = mock.Mock()
    mock_logging.StreamHandler = mock_streamhandler
    streamhandler_instance = mock_streamhandler.return_value
    mock_formatter = mock.Mock()
    streamhandler_instance.setFormatter = mock_formatter

    cli.main()

    mock_streamhandler.assert_called_once_with(mock_sys.stdout)
    mock_formatter.assert_called_once()
    mock_tree.assert_called_once()
    config_arg = mock_tree.call_args.kwargs["config"]
    assert config_arg.fail_fast is True


@mock.patch("gitlabber.cli.GitlabTree")
def test_args_include(mock_tree: mock.Mock) -> None:
    args_mock = create_mock_args({"print_format": PrintFormat.YAML})
    cli.parse_args = args_mock

    print_tree_mock = mock.Mock()
    mock_tree.return_value.print_tree = print_tree_mock
    mock_tree.return_value.is_empty = mock.Mock(return_value=False)

    cli.main()

    print_tree_mock.assert_called_once_with(PrintFormat.YAML)


def test_validate_path():
    assert "/test" == cli.validate_path("/test/")
    assert "/test" == cli.validate_path("/test")
    assert "/" == cli.validate_path("//")
    assert "." == cli.validate_path("./")
    assert "." == cli.validate_path(".")


@mock.patch("gitlabber.cli.GitlabTree")
def test__missing_token(mock_tree):
    args_mock = mock.Mock()
    args_mock.return_value = Node(
        type="test", name="test", version=None, verbose=None, include="", exclude="", url="test_url", token=None, print=True, dest=".")
    cli.parse_args = args_mock

    with pytest.raises(SystemExit):
        cli.main()


@mock.patch("gitlabber.cli.GitlabTree")
def test_missing_url(mock_tree):
    args_mock = mock.Mock()
    args_mock.return_value = Node(
        type="test", name="test", version=None, verbose=None, include="", exclude="", url=None, token="some_token", print=True, dest=".")
    cli.parse_args = args_mock

    with pytest.raises(SystemExit):
        cli.main()


@mock.patch("gitlabber.cli.GitlabTree")
def test_empty_tree(mock_tree: mock.Mock) -> None:
    args_mock = create_mock_args()
    cli.parse_args = args_mock

    with pytest.raises(SystemExit):
        cli.main()


@mock.patch("gitlabber.cli.GitlabTree")
def test_missing_dest(mock_tree, capsys):
    args_mock = mock.Mock()
    args_mock.return_value = Node(
        type="test", name="test", version=None, verbose=None, include="", exclude="", url="test_url", token="test_token", method=CloneMethod.SSH, naming=FolderNaming.NAME, archived=ArchivedResults.INCLUDE, file=None, concurrency=1, recursive=False, disble_progress=True, print=False, dest=None, group_search=None, git_options=None)
    cli.parse_args = args_mock
    mock_tree.return_value.is_empty = mock.Mock(return_value=False)

    with pytest.raises(SystemExit):
        cli.main()
    out, err = capsys.readouterr()
    assert "Please specify a destination" in out


