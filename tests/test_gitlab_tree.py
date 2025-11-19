from gitlabber.method import CloneMethod
import tests.gitlab_test_utils as gitlab_util
import tests.io_test_util as output_util
from gitlabber.archive import ArchivedResults
import pytest
from unittest import mock
from gitlab.exceptions import GitlabGetError

def test_load_tree(monkeypatch: pytest.MonkeyPatch) -> None:
    gl = gitlab_util.create_test_gitlab(monkeypatch)
    gl.load_tree()
    gl.print_tree()
    gitlab_util.validate_tree(gl.root)


def test_filter_tree_include_positive(monkeypatch):
    gl = gitlab_util.create_test_gitlab(monkeypatch, includes=["/group**"])
    gl.load_tree()
    gitlab_util.validate_tree(gl.root)


def test_filter_tree_include_negative(monkeypatch):
    gl = gitlab_util.create_test_gitlab(monkeypatch, includes=["/no_match**"])
    gl.load_tree()
    assert gl.root.is_leaf is True
    assert len(gl.root.children) == 0


def test_filter_tree_include_deep_positive(monkeypatch):
    gl = gitlab_util.create_test_gitlab(monkeypatch, includes=["/group/subgroup/project"])
    gl.load_tree()
    assert gl.root.is_leaf is False
    assert len(gl.root.children) == 1
    assert len(gl.root.children[0].children) == 1
    assert len(gl.root.children[0].children[0].children) == 1
    assert gl.root.children[0].children[0].children[0].is_leaf is True


def test_filter_tree_exclude_positive(monkeypatch):
    gl = gitlab_util.create_test_gitlab(monkeypatch, excludes=["/group**"])
    gl.load_tree()
    assert gl.root.is_leaf is True
    assert len(gl.root.children) == 0


def test_filter_tree_exclude_deep_positive(monkeypatch):
    gl = gitlab_util.create_test_gitlab(monkeypatch, excludes=["/group/subgroup/project**"])
    gl.load_tree()
    assert gl.root.is_leaf is False
    assert gl.root.height == 2
    assert gl.root.children[0].height == 1


def test_filter_tree_exclude_negative(monkeypatch):
    gl = gitlab_util.create_test_gitlab(monkeypatch, excludes=["/no_match**"])
    gl.load_tree()
    gitlab_util.validate_tree(gl.root)
    
def test_print_tree_json(monkeypatch):
    gl = gitlab_util.create_test_gitlab(monkeypatch)
    gl.load_tree()
    from gitlabber.format import PrintFormat
    import json
    with output_util.captured_output() as (out, err):
        gl.print_tree(PrintFormat.JSON)
        output = json.loads(out.getvalue())
        with open(gitlab_util.JSON_TEST_OUTPUT_FILE, 'r') as jsonFile:
            output_file = json.load(jsonFile)
            assert json.dumps(output_file, sort_keys=True, indent=2) == json.dumps(
                output, sort_keys=True, indent=2)


def test_print_tree_yaml(monkeypatch):
    gl = gitlab_util.create_test_gitlab(monkeypatch)
    gl.load_tree()
    from gitlabber.format import PrintFormat
    import yaml
    with output_util.captured_output() as (out, err):
        gl.print_tree(PrintFormat.YAML)
        output = yaml.safe_load(out.getvalue())
        with open(gitlab_util.YAML_TEST_OUTPUT_FILE, 'r') as yamlFile:
            output_file = yaml.safe_load(yamlFile)
            assert yaml.dump(output_file) == yaml.dump(output)


def test_load_tree_from_file(monkeypatch):
    gl = gitlab_util.create_test_gitlab(
        monkeypatch, in_file=gitlab_util.JSON_TEST_OUTPUT_FILE)
    gl.load_tree()
    gitlab_util.validate_tree(gl.root)


def test_empty_tree(monkeypatch):
    gl = gitlab_util.create_test_gitlab(monkeypatch, excludes=["/group**"])
    gl.load_tree()
    assert gl.is_empty() is True

def test_archive_included(monkeypatch):
    gl = gitlab_util.create_test_gitlab_with_archived(monkeypatch, archived=ArchivedResults.INCLUDE.api_value)
    gl.load_tree()
    assert gl.root.is_leaf is False
    assert len(gl.root.children) == 2
    assert len(gl.root.children[0].children) == 2
    assert len(gl.root.children[0].children[0].children) == 2

def test_archive_excluded(monkeypatch):
    gl = gitlab_util.create_test_gitlab_with_archived(monkeypatch, archived=ArchivedResults.EXCLUDE.api_value)
    
    gl.load_tree()
    assert gl.root.is_leaf is False
    assert len(gl.root.children) == 1
    assert len(gl.root.children[0].children) == 2
    assert len(gl.root.children[0].children[0].children) == 1
    
    assert "_archived_" not in gl.root.children[0].name
    assert "_archived_" not in gl.root.children[0].children[0].name
    assert "_archived_" not in gl.root.children[0].children[0].children[0].name

def test_archive_only(monkeypatch):
    gl = gitlab_util.create_test_gitlab_with_archived(monkeypatch, archived=ArchivedResults.ONLY.api_value)
    
    gl.load_tree()
    gl.print_tree()
    assert gl.root.is_leaf is False
    assert len(gl.root.children) == 1
    assert len(gl.root.children[0].children) == 2
    assert len(gl.root.children[0].children[0].children) == 1
    
    assert "_archived_" in gl.root.children[0].name
    assert "_archived_" in gl.root.children[0].children[0].children[0].name

def test_get_ca_path(monkeypatch):
    import os
    from gitlabber import gitlab_tree
    os.environ["REQUESTS_CA_BUNDLE"] = "/tmp"
    result = gitlab_tree.GitlabTree.get_ca_path()
    assert result == "/tmp"
    del os.environ['REQUESTS_CA_BUNDLE']

    os.environ["CURL_CA_BUNDLE"] = "/tmp2"
    result = gitlab_tree.GitlabTree.get_ca_path()
    assert result == "/tmp2"
    del os.environ['CURL_CA_BUNDLE']

    result = gitlab_tree.GitlabTree.get_ca_path()
    assert result

def test_shared_included(monkeypatch):
    gl = gitlab_util.create_test_gitlab_with_shared(monkeypatch, with_shared=True)

    gl.load_tree()
    gl.print_tree()
    assert gl.root.is_leaf is False
    assert len(gl.root.children) == 1
    assert len(gl.root.children[0].children) == 2

    assert "project" in gl.root.children[0].children[0].name
    assert "_shared_" in gl.root.children[0].children[1].name


def test_shared_excluded(monkeypatch):
    gl = gitlab_util.create_test_gitlab_with_shared(monkeypatch, with_shared=False)

    gl.load_tree()
    gl.print_tree()
    assert gl.root.is_leaf is False
    assert len(gl.root.children) == 1
    assert len(gl.root.children[0].children) == 1

    assert "project" in gl.root.children[0].children[0].name
    
    
def test_hide_token_from_project_url(monkeypatch):
    gl = gitlab_util.create_test_gitlab(monkeypatch, hide_token=True, method=CloneMethod.HTTP)
    gl.load_tree()
    gl.print_tree()
    assert 'gitlab-token:xxx@' not in gl.root.children[0].children[0].children[0].url


def test_get_subgroups_404_error(monkeypatch):
    gl = gitlab_util.create_test_gitlab(monkeypatch)

    # Create mock group and subgroup
    mock_group = mock.Mock()
    mock_group.name = "mock_group"
    mock_group.id = 123
    
    # Create a mock subgroup definition that will be returned by list()
    mock_subgroup_def = mock.Mock()
    mock_subgroup_def.id = 456
    
    # Make subgroups.list return our mock subgroup definition
    mock_group.subgroups.list.return_value = [mock_subgroup_def]

    # This is the function that will raise the 404 when trying to get the subgroup
    def mock_get_subgroup(id):
        raise GitlabGetError(response_code=404, error_message="Not Found")

    # Patch the groups.get method
    monkeypatch.setattr(gl.gitlab.groups, "get", mock_get_subgroup)

    with mock.patch("gitlabber.gitlab_tree.log.error") as mock_log_error:
        gl.get_subgroups(mock_group, gl.root)
        # New format includes suggestion, but log.error gets the base message
        # The suggestion is included in the exception, not the log
        mock_log_error.assert_called_once()
        call_args = mock_log_error.call_args
        assert "404 error while getting subgroup" in call_args[0][0]
        assert "mock_group" in call_args[0][0]
        assert "Message: Not Found" in call_args[0][0]

def test_hide_token_in_project_url_both_cases(monkeypatch):
    test_token = "test-token-123"
    
    # Create two instances to test both cases
    gl_hidden = gitlab_util.create_test_gitlab(monkeypatch, 
                                             hide_token=True, 
                                             method=CloneMethod.HTTP,
                                             token=test_token)
                                             
    gl_visible = gitlab_util.create_test_gitlab(monkeypatch, 
                                              hide_token=False, 
                                              method=CloneMethod.HTTP,
                                              token=test_token)

    # Create mock project
    mock_project = mock.Mock()
    mock_project.name = "test-project"
    mock_project.path = "test-project"
    mock_project.ssh_url_to_repo = "git@gitlab.com:group/test-project.git"
    mock_project.http_url_to_repo = "https://gitlab.com/group/test-project.git"

    # Test with hide_token=True
    with mock.patch("gitlabber.gitlab_tree.log.debug") as mock_log_debug_hidden:
        gl_hidden.add_projects(gl_hidden.root, [mock_project])
        project_node_hidden = gl_hidden.root.children[0]
        
        # Verify token is not in URL
        assert project_node_hidden.url == "https://gitlab.com/group/test-project.git"
        mock_log_debug_hidden.assert_any_call("Hiding token from project url: %s", 
                                            project_node_hidden.url)

    # Test with hide_token=False
    with mock.patch("gitlabber.gitlab_tree.log.debug") as mock_log_debug_visible:
        gl_visible.add_projects(gl_visible.root, [mock_project])
        project_node_visible = gl_visible.root.children[0]
        
        expected_url = f"https://gitlab-token:{test_token}@gitlab.com/group/test-project.git"
        assert project_node_visible.url == expected_url
        mock_log_debug_visible.assert_any_call("Generated URL: %s", expected_url)

@mock.patch('gitlabber.gitlab_tree.Gitlab')
def test_get_projects_404(mock_gitlab: mock.Mock) -> None:
    error = GitlabGetError(response_code=404)
    mock_gitlab.groups.list.side_effect = error
    gl = gitlab_util.create_test_gitlab(mock_gitlab)
    gl.load_tree()
    assert gl.root.height == 0

@mock.patch('gitlabber.gitlab_tree.Gitlab')
def test_load_user_tree(mock_gitlab):
    gl = gitlab_util.create_test_gitlab(mock_gitlab)
    
    # Create mock user
    mock_user = mock.Mock()
    mock_user.id = 123
    mock_user.username = "testuser"
    
    # Create mock projects
    mock_project1 = mock.Mock()
    mock_project1.name = "project1"
    mock_project1.path = "project1"
    mock_project1.ssh_url_to_repo = "git@gitlab.my.com:testuser/project1.git"
    mock_project1.http_url_to_repo = "http://gitlab.my.com/testuser/project1.git"
    
    mock_project2 = mock.Mock()
    mock_project2.name = "project2"
    mock_project2.path = "project2"
    mock_project2.ssh_url_to_repo = "git@gitlab.my.com:testuser/project2.git"
    mock_project2.http_url_to_repo = "http://gitlab.my.com/testuser/project2.git"
    
    # Mock the user object and its projects
    gl.gitlab.user = mock_user
    gl.gitlab.users.get.return_value = mock_user
    mock_user.projects.list.return_value = [mock_project1, mock_project2]
    
    # Set user_projects to True to trigger load_user_tree
    gl.user_projects = True
    
    # Load the tree
    gl.load_tree()
    
    # Verify the tree structure
    assert gl.root.name == ""
    assert len(gl.root.children) == 1
    assert gl.root.children[0].name == "testuser-personal-projects"
    assert len(gl.root.children[0].children) == 2
    assert gl.root.children[0].children[0].name == "project1"
    assert gl.root.children[0].children[1].name == "project2"