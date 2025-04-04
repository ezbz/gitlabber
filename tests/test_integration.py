import os
import json
from gitlabber import __version__ as VERSION
import tests.gitlab_test_utils as gitlab_util
import tests.io_test_util as io_util
import pytest
import coverage
from typing import cast
import sys
import subprocess
import importlib
from io import StringIO
from contextlib import contextmanager
from gitlabber.gitlab_tree import GitlabTree
from gitlabber.method import CloneMethod
from gitlabber.auth import NoAuthProvider

coverage.process_startup()

# Check if gitlabber module is importable
try:
    importlib.import_module("gitlabber")
    print("gitlabber module is importable")
except ImportError as e:
    print(f"gitlabber module is not importable: {e}")

@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err

@pytest.mark.integration_test
def test_help():
    output = io_util.execute(["-h"])
    assert "usage:" in output
    assert "examples:" in output
    assert "positional arguments:" in output
    assert "Gitlabber - clones or pulls entire groups/projects tree from gitlab" in output

@pytest.mark.integration_test
def test_version():
    output = io_util.execute(["--version"])
    assert VERSION in output

@pytest.mark.integration_test
def test_file_input() -> None:
    os.environ['GITLAB_URL'] = 'http://gitlab.my.com/'
    
    # Create GitlabTree instance directly
    tree = GitlabTree(
        url='http://gitlab.my.com/',
        token='xxx',
        method=CloneMethod.SSH,
        in_file=gitlab_util.YAML_TEST_INPUT_FILE,
        auth_provider=NoAuthProvider()  # Skip authentication for testing
    )
    
    # Load and print the tree
    with captured_output() as (out, err):
        tree.load_tree()
        tree.print_tree()
        output = out.getvalue().strip()
    
    # Print debug information
    print(f"Output: {output}")
    
    with open(gitlab_util.TREE_TEST_OUTPUT_FILE, 'r') as tree_file:
        expected_output = tree_file.read().strip()
        print(f"Expected: {expected_output}")
        assert expected_output == output
