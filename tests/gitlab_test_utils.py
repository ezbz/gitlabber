import pytest
import json
from unittest import mock
from gitlabber import gitlab_tree

URL = "http://gitlab.my.com/"
TOKEN = "MOCK_TOKEN"
GROUP_URL = "http://gitlab.my.com/group"
GROUP_NAME = "group"

SUBGROUP_URL = "http://gitlab.my.com/group/subgroup"
SUBGROUP_NAME = "subgroup"

PROJECT_URL = "http://gitlab.my.com/group/subgroup/project/project.git"
PROJECT_NAME = "project"

YAML_TEST_INPUT_FILE = "tests/test-input.yaml"
YAML_TEST_OUTPUT_FILE = "tests/test-output.yaml"
JSON_TEST_OUTPUT_FILE = "tests/test-output.json"
TREE_TEST_OUTPUT_FILE = "tests/test-output.tree"


class MockNode:
    def __init__(self, id, name, url, subgroups=mock.MagicMock(), projects=mock.MagicMock(), parent_id=None):
        self.id = id
        self.name = name
        self.path = name
        self.url = url
        self.web_url = url
        self.ssh_url_to_repo = url
        self.http_url_to_repo = url
        self.subgroups = subgroups
        self.projects = projects
        self.parent_id = parent_id


class Listable:
    def __init__(self, list_result, get_results=None, archive_result=None):
        self.list_result = list_result
        self.get_results = get_results
        self.archive_result = archive_result

    def list(self, as_list=False, archived=None, top_level_only=False):
        if archived is None:
            return [self.list_result, self.archive_result] if self.archive_result is not None else [self.list_result]
        elif archived is True:
            return [self.archive_result]
        else:
            return [self.list_result]

    def get(self, id, lazy=False):
        return self.get_results[id]


def validate_root(root):
    assert root.is_leaf is False
    assert root.name == ""
    assert root.url == "http://gitlab.my.com/"
    assert len(root.children) == 1
    assert root.height == 3


def validate_group(group):
    assert group.name == GROUP_NAME
    assert group.url == GROUP_URL
    assert group.is_leaf is False
    assert len(group.children) == 1
    assert group.height == 2


def validate_subgroup(subgroup):
    assert subgroup.name == SUBGROUP_NAME
    assert subgroup.url == SUBGROUP_URL
    assert subgroup.is_leaf is False
    assert len(subgroup.children) == 1
    assert subgroup.height == 1


def validate_project(project):
    assert project.name == PROJECT_NAME
    assert project.url == PROJECT_URL
    assert project.is_leaf is True
    assert len(project.children) == 0


def validate_tree(root):
    validate_root(root)
    validate_group(root.children[0])
    validate_subgroup(root.children[0].children[0])
    validate_project(root.children[0].children[0].children[0])


def append_node(nodes, *args, **kwargs):
    node = MockNode(len(nodes), *args, **kwargs)
    nodes.append(node)
    return node


def create_test_gitlab(monkeypatch, includes=None, excludes=None, in_file=None):
    gl = gitlab_tree.GitlabTree(
        URL, TOKEN, "ssh", "name", includes=includes, excludes=excludes, in_file=in_file)
    nodes = []
    projects = Listable(append_node(nodes, PROJECT_NAME, PROJECT_URL))
    subgroup_node = append_node(nodes, SUBGROUP_NAME, SUBGROUP_URL,
                                projects=projects)
    subgroups = Listable(subgroup_node)
    groups = Listable(append_node(nodes, GROUP_NAME, GROUP_URL,
                                  subgroups=subgroups), nodes)
    monkeypatch.setattr(gl.gitlab, "groups", groups)
    return gl


def create_test_gitlab_with_toplevel_subgroups(monkeypatch):
    gl = gitlab_tree.GitlabTree(URL, TOKEN, "ssh", "path")
    nodes = []
    groups = Listable([append_node(nodes, GROUP_NAME, GROUP_URL),
                       append_node(nodes, GROUP_NAME, GROUP_URL, parent_id=1)],
                       nodes)
    monkeypatch.setattr(gl.gitlab, "groups", groups)
    return gl


def create_test_gitlab_with_archived(monkeypatch, includes=None, excludes=None, in_file=None, archived=None):
    gl = gitlab_tree.GitlabTree(
        URL, TOKEN, "ssh", "name", includes=includes, excludes=excludes, in_file=in_file, archived=archived)
    nodes = []
    project_node = append_node(nodes, PROJECT_NAME, PROJECT_URL)
    archived_project_node = append_node(nodes, "_archived_" + PROJECT_NAME,
                                        "_archived_" + PROJECT_URL)
    projects = Listable(project_node, archive_result=archived_project_node)
    subgroup_node = append_node(nodes, SUBGROUP_NAME, SUBGROUP_URL,
                                projects=projects)
    archived_subgroup_node = append_node(nodes, "_archived_" + SUBGROUP_NAME,
                                         "_archived_" + SUBGROUP_URL,
                                         projects=projects)
    subgroups = Listable(subgroup_node, archive_result=archived_subgroup_node)
    group_node = append_node(nodes, GROUP_NAME, GROUP_URL,
                             subgroups=subgroups)
    archived_group_node = append_node(nodes, "_archived_" + GROUP_NAME,
                                      "_archived_" + GROUP_URL,
                                      subgroups=subgroups)
    groups = Listable(group_node, archive_result=archived_group_node,
                      get_results=nodes)
    monkeypatch.setattr(gl.gitlab, "groups", groups)
    # gl.print_tree()
    return gl
