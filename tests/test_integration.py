import os
import json
from gitlabber import __version__ as VERSION
import tests.gitlab_test_utils as gitlab_util
import tests.io_test_util as io_util
import pytest
import coverage
coverage.process_startup()

@pytest.mark.integration_test
def test_help():
    output = io_util.execute(["-h"])
    assert "usage:" in output
    assert "examples:" in output
    assert "positional arguments:" in output
    assert "optional arguments:" in output
    assert "Gitlabber - clones or pulls entire groups/projects tree from gitlab" in output

@pytest.mark.integration_test
def test_version():
    output = io_util.execute(["--version"])
    assert VERSION in output

@pytest.mark.integration_test
def test_file_input():
    os.environ['GITLAB_URL'] = 'http://gitlab.my.com/'
    output = io_util.execute(["-f", gitlab_util.YAML_TEST_INPUT_FILE, "-p", '-t', 'xxx'])
    with open(gitlab_util.TREE_TEST_OUTPUT_FILE, 'r') as treeFile:
        assert treeFile.read().strip() == output.strip()
