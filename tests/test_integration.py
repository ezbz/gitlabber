import os
import sys
import subprocess
import yaml
from gitlabber import __version__ as VERSION
import tests.gitlab_test_utils as gitlab_util
import pytest
import coverage
coverage.process_startup()

def execute(args):
    cmd = [sys.executable, '-m', 'gitlabber']
    cmd.extend(args)
    os.environ['GITLAB_URL'] = 'http://gitlab.my.com/'
    with subprocess.Popen(cmd, stdout=subprocess.PIPE, env=os.environ.copy()) as process:
        outs, err = process.communicate(timeout=3)    
        process.wait()
        return outs.decode('utf-8')
    

def test_help():
    output = execute(["-h"])
    assert "usage:" in output
    assert "examples:" in output
    assert "positional arguments:" in output
    assert "optional arguments:" in output
    assert "Gitlabber - clones or pulls entire groups/projects tree from gitlab" in output


def test_help():
    output = execute(["--version"])
    assert VERSION in output

def test_file_input():
    output = execute(["-f", gitlab_util.YAML_TEST_INPUT_FILE, "-p"])
    with open(gitlab_util.TREE_TEST_OUTPUT_FILE, 'r') as treeFile:
        assert treeFile.read().strip() == output.strip()