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
    def __init__(self, type, id, name, url, subgroups=mock.MagicMock(), projects=mock.MagicMock(), parent_id=None, archived=0, shared=False, group_search=None):
        self.type = type
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
        self.archived = archived
        self.shared = shared
        self.group_search = group_search


class Listable:
    def __init__(self, *nodes: MockNode):
        self.nodes = nodes

    def list(self, as_list=False, archived=None, with_shared=True, get_all=True, search=None):
        filtered = filter(lambda it: self.is_included(it, archived, with_shared), self.nodes)
        return list(filtered)

    def is_included(self, node: MockNode, archived, shared):
        if node.shared and shared is False:
            return False
        elif node.archived and archived is False:
            return False
        elif not node.archived and archived is True:
            return False
        else:
            return True

    def get(self, id):
        if self.get_result is not None:
            return self.get_result
        else:
            return self.list_result
class Tree:
    def __init__(self, roots: Listable):
        self.all_nodes = []
        for root_node in roots.nodes:
            self.all_nodes.extend(self.get_all_nodes(root_node))
        self.roots = roots

    def get(self, id):
        return next(filter(lambda it: it.id == id, self.all_nodes))

    def list(self, as_list=False, archived=None, with_shared=True, get_all=True, search=None):
        return self.roots.list(as_list, archived, with_shared)

    def get_all_nodes(self, node: MockNode):
        nodes = [node]
        if node.subgroups:
            for sub_node in node.subgroups.nodes:
                nodes.extend(self.get_all_nodes(sub_node))
        if node.projects:
            for sub_node in node.projects.nodes:
                nodes.extend(self.get_all_nodes(sub_node))
        return nodes

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

def create_test_gitlab(monkeypatch, includes=None, excludes=None, in_file=None):
    gl = gitlab_tree.GitlabTree(
        URL, TOKEN, "ssh", "name", includes=includes, excludes=excludes, in_file=in_file)
    projects = Listable(MockNode("project", 2, PROJECT_NAME, PROJECT_URL))
    groups = Listable(
            MockNode("group", 2, GROUP_NAME, GROUP_URL, subgroups=Listable(
            MockNode("subgroup", 3, SUBGROUP_NAME, SUBGROUP_URL, projects=projects)
        ))
    )
    monkeypatch.setattr(gl.gitlab, "groups", Tree(groups))
    return gl


def create_test_gitlab_with_toplevel_subgroups(monkeypatch):
    gl = gitlab_tree.GitlabTree(URL, TOKEN, "ssh", "path")
    groups = Listable(
        MockNode("group", 2, GROUP_NAME, GROUP_URL),
        MockNode("group", 3, GROUP_NAME, GROUP_URL, parent_id=1)
    )
    monkeypatch.setattr(gl.gitlab, "groups", Tree(groups))
    return gl


def create_test_gitlab_with_archived(monkeypatch, includes=None, excludes=None, in_file=None, archived=False):
    gl = gitlab_tree.GitlabTree(
        URL, TOKEN, "ssh", "name", includes=includes, excludes=excludes, in_file=in_file, archived=archived)
    projects = Listable(
        MockNode("project", 11, PROJECT_NAME, PROJECT_URL),
        MockNode("project", 12, "_archived_" + PROJECT_NAME, "_archived_" + PROJECT_URL, archived=1)
    )
    monkeypatch.setattr(gl.gitlab, "groups", Tree(Listable(
        MockNode("group", 13, GROUP_NAME, GROUP_URL, subgroups=Listable(
            MockNode("subgroup", 14, SUBGROUP_NAME, SUBGROUP_URL, projects=projects),
            MockNode("subgroup", 15, SUBGROUP_NAME, SUBGROUP_URL, projects=projects)
        )),
        MockNode("group", 16, "_archived_" + GROUP_NAME, "_archived_" + GROUP_URL, archived=1, subgroups=Listable(
            MockNode("subgroup", 17, SUBGROUP_NAME, SUBGROUP_URL, projects=projects),
            MockNode("subgroup", 18, SUBGROUP_NAME, SUBGROUP_URL, projects=projects)
        ))
    )))
    return gl

def create_test_gitlab_with_shared(monkeypatch, includes=None, excludes=None, in_file=None, with_shared=True):
    gl = gitlab_tree.GitlabTree(
        URL, TOKEN, "ssh", "name", includes=includes, excludes=excludes, in_file=in_file, include_shared=with_shared)

    projects = Listable(
        MockNode("project", 19, PROJECT_NAME, PROJECT_URL),
        MockNode("project", 20, "_shared_" + PROJECT_NAME, "_shared_" + PROJECT_URL, shared=True)
    )
    monkeypatch.setattr(gl.gitlab, "groups", Tree(Listable(
        MockNode("group", 21, GROUP_NAME, GROUP_URL, projects=projects)
    )))
    return gl