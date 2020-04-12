
from gitlabber import cli
from gitlabber import __version__ as VERSION
import tests.output_test_utils as output_util

from gitlabber.format import PrintFormat
from unittest import mock
from anytree import Node
import pytest

def exit():
    import sys
    sys.exit()

def test_args_version():
    args_mock = mock.Mock()
    args_mock.return_value = Node(name="test",version=True)
    cli.parse_args = args_mock
    
    with output_util.captured_output() as (out, err):
        with pytest.raises(SystemExit):
            cli.main()
            assert VERSION == out.getvalue()


@mock.patch("gitlabber.cli.logging")
@mock.patch("gitlabber.cli.sys")
@mock.patch("gitlabber.cli.os")
@mock.patch("gitlabber.cli.log")
@mock.patch("gitlabber.cli.GitlabTree")
def test_args_logging(mock_tree, mock_log, mock_os, mock_sys, mock_logging):
    args_mock = mock.Mock()
    args_mock.return_value = Node(
        name="test", version=None, debug=True, include="", exclude="", url="test_url", token="test_token", file=None, print=None, dest=".")
    cli.parse_args = args_mock

    mock_streamhandler = mock.Mock()
    mock_logging.StreamHandler = mock_streamhandler
    streamhandler_instance = mock_streamhandler.return_value
    mock_formatter = mock.Mock()
    streamhandler_instance.setFormatter = mock_formatter

    cli.main()

    mock_streamhandler.assert_called_once_with(mock_sys.stdout)
    mock_formatter.assert_called_once()


@mock.patch("gitlabber.cli.GitlabTree")
def test_args_include(mock_tree):
    inc_groups = "/inc**,/inc**"
    exc_groups = "/exc**,/exc**"
    args_mock = mock.Mock()
    args_mock.return_value = Node(
        name="test", version=None, debug=None, include=inc_groups, exclude=exc_groups, url="test_url", token="test_token", file=None, print=None, dest=".")
    cli.parse_args = args_mock
    
    split_mock = mock.Mock()
    cli.split = split_mock

    mock_tree.return_value.is_empty = mock.Mock(return_value = False)

    cli.main()
    split_mock.assert_has_calls([mock.call(inc_groups), mock.call(exc_groups)])


@mock.patch("gitlabber.cli.GitlabTree")
def test_args_include(mock_tree):
    args_mock = mock.Mock()
    args_mock.return_value = Node(
        name="test", version=None, debug=None, include="", exclude="", url="test_url", token="test_token", file=None, print=True, dest=".", print_format=PrintFormat.YAML)
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
def test_empty_tree(mock_tree):
    args_mock = mock.Mock()
    args_mock.return_value = Node(
        name="test", version=None, debug=None, include="", exclude="", url="test_url", token="test_token", file=None, print=True, dest=".")
    cli.parse_args = args_mock

    with pytest.raises(SystemExit):
        cli.main()
