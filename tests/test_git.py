

from gitlabber import git
from gitlabber.git import GitAction
from unittest import mock
from anytree import Node
import pytest

DEST="./test_dest"
GROUP_PATH = "/group"
SUBGROUP_PATH = "/group/subgroup"
PROJECT_PATH = "/group/subgroup/project"

def create_tree():
    root = Node(name="root")
    group = Node(name="group", root_path=GROUP_PATH, parent=root)
    subgroup = Node(name="subgroup", root_path=SUBGROUP_PATH, parent=group)
    Node(name="project1", root_path=PROJECT_PATH, parent=subgroup)
    return root


@mock.patch('gitlabber.git.os')
@mock.patch('gitlabber.git.git')
@mock.patch('gitlabber.git.clone_or_pull_project')
@mock.patch('gitlabber.git.progress')
def test_create_new_user_dir(mock_progress, mock_clone_or_pull_project, mock_git, mock_os):
    # git.git = mock.MagicMock()
    
    mock_os.path.exists.return_value = False

    root = create_tree()
    git.sync_tree(root,DEST)
    
    assert 3 == mock_os.path.exists.call_count
    mock_os.path.exists.assert_has_calls(
        [mock.call(DEST+GROUP_PATH), mock.call(DEST+SUBGROUP_PATH), mock.call(DEST+PROJECT_PATH)])

    assert 3 == mock_os.makedirs.call_count
    mock_os.makedirs.assert_has_calls(
        [mock.call(DEST+GROUP_PATH), mock.call(DEST+SUBGROUP_PATH), mock.call(DEST+PROJECT_PATH)])

    assert 1 == git.clone_or_pull_project.call_count


@mock.patch('gitlabber.git.git')
def test_is_git_repo_true(mock_git):
    mock_repo = mock.Mock()
    mock_git.Repo = mock_repo
    git.is_git_repo("dummy_dir")
    assert 1 == mock_git.Repo.call_count
    mock_git.Repo.assert_called_once_with("dummy_dir")


def test_is_git_repo_throws():
    with pytest.raises(git.git.exc.NoSuchPathError):
        git.is_git_repo("dummy_dir")

@mock.patch('gitlabber.git.git')
def test_pull_repo(mock_git):
    mock_repo = mock.Mock()
    mock_git.Repo = mock_repo
    repo_instance = mock_git.Repo.return_value
    git.is_git_repo = mock.MagicMock(return_value=True)

    git.clone_or_pull_project(GitAction(Node(name="test"), "dummy_dir"))
    mock_git.Repo.assert_called_once_with("dummy_dir")
    repo_instance.remotes.origin.pull.assert_called_once()


@mock.patch('gitlabber.git.git')
def test_clone_repo(mock_git):
    mock_repo = mock.Mock()
    mock_git.Repo = mock_repo
    git.is_git_repo = mock.MagicMock(return_value=False)

    git.clone_or_pull_project(
        GitAction(Node(name="dummy_url", url="dummy_url"), "dummy_dir"))

    mock_git.Repo.clone_from.assert_called_once_with("dummy_url", "dummy_dir")

@mock.patch('gitlabber.git.git')
def test_clone_repo_recursive(mock_git):
    mock_repo = mock.Mock()
    mock_git.Repo = mock_repo
    git.is_git_repo = mock.MagicMock(return_value=False)

    git.clone_or_pull_project(
        GitAction(Node(name="dummy_url", url="dummy_url"), "dummy_dir", recursive=True))

    mock_git.Repo.clone_from.assert_called_once_with("dummy_url", "dummy_dir", multi_options=['--recursive'])

@mock.patch('gitlabber.git.git')
def test_pull_repo_recursive(mock_git):
    mock_repo = mock.Mock()
    mock_git.Repo = mock_repo
    repo_instance = mock_git.Repo.return_value
    git.is_git_repo = mock.MagicMock(return_value=True)

    git.clone_or_pull_project(GitAction(Node(name="test"), "dummy_dir", recursive=True))
    mock_git.Repo.assert_called_once_with("dummy_dir")
    repo_instance.remotes.origin.pull.assert_called_once()
    repo_instance.submodule_update.assert_called_once_with(recursive=True)

@mock.patch('gitlabber.git.git')
def test_pull_repo_interrupt(mock_git):
    mock_repo = mock.Mock()
    mock_git.Repo = mock_repo
    git.is_git_repo = mock.MagicMock(return_value=True)

    repo_instance = mock_git.Repo.return_value
    repo_instance.remotes.origin.pull.side_effect=KeyboardInterrupt('pull test keyboard interrupt')

    with pytest.raises(SystemExit):
        git.clone_or_pull_project(GitAction(
            Node(name="dummy_url", url="dummy_url"), "dummy_dir"))

    mock_git.Repo.assert_called_once_with("dummy_dir")
    repo_instance.remotes.origin.pull.assert_called_once()

@mock.patch('gitlabber.git.git')
def test_clone_repo_interrupt(mock_git):
    mock_repo = mock.Mock()
    mock_git.Repo = mock_repo
    git.is_git_repo = mock.MagicMock(return_value=False)
    mock_git.Repo.clone_from.side_effect=KeyboardInterrupt('clone test keyboard interrupt')

    with pytest.raises(SystemExit):
        git.clone_or_pull_project(GitAction(
            Node(name="dummy_url", url="dummy_url"), "dummy_dir"))

    mock_git.Repo.clone_from.assert_called_once_with("dummy_url", "dummy_dir")
