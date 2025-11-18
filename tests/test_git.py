
"""Tests for git operations using improved mocking patterns."""
from gitlabber import git
from gitlabber.git import GitAction
from gitlabber.exceptions import GitlabberGitError
from unittest import mock
from anytree import Node
import pytest
import git as gitpython
from tests.test_helpers import TreeBuilder, MockGitRepo


@mock.patch('gitlabber.git.clone_or_pull_project')
def test_create_new_user_dir(mock_clone_or_pull_project, tmp_path):
    """Test that sync_tree creates directory structure correctly."""
    root = TreeBuilder.create_simple_tree()
    git.sync_tree(root, str(tmp_path))

    assert (tmp_path / "group").is_dir()
    assert (tmp_path / "group" / "subgroup").is_dir()
    assert (tmp_path / "group" / "subgroup" / "project").is_dir()

    mock_clone_or_pull_project.assert_called_once()


@mock.patch('gitlabber.git.git')
def test_is_git_repo_true(mock_git):
    """Test is_git_repo returns True for valid git repository."""
    mock_git_repo = MockGitRepo.create_mock_repo(is_git_repo=True)
    mock.patch('gitlabber.git.git', mock_git_repo).start()
    
    git.is_git_repo("dummy_dir")
    assert mock_git_repo.Repo.call_count == 1
    mock_git_repo.Repo.assert_called_once_with("dummy_dir")


def test_is_git_repo_throws():
    with pytest.raises(git.git.exc.NoSuchPathError):
        git.is_git_repo("dummy_dir")

@mock.patch('gitlabber.git.git')
@mock.patch('gitlabber.git.is_git_repo')
def test_pull_repo(mock_is_git_repo, mock_git):
    """Test pulling an existing repository."""
    mock_git_repo = MockGitRepo.create_mock_repo(is_git_repo=True)
    mock.patch('gitlabber.git.git', mock_git_repo).start()
    mock_is_git_repo.return_value = True

    action = TreeBuilder.create_git_action(
        TreeBuilder.create_simple_tree().children[0].children[0].children[0],
        "dummy_dir"
    )
    git.clone_or_pull_project(action)
    
    mock_git_repo.Repo.assert_called_once_with("dummy_dir")
    mock_git_repo.Repo.return_value.remotes.origin.pull.assert_called_once()


@mock.patch('gitlabber.git.git')
@mock.patch('gitlabber.git.is_git_repo')
def test_clone_repo(mock_is_git_repo, mock_git):
    """Test cloning a new repository."""
    mock_git_repo = MockGitRepo.create_mock_repo(is_git_repo=False)
    mock.patch('gitlabber.git.git', mock_git_repo).start()
    mock_is_git_repo.return_value = False

    action = TreeBuilder.create_git_action(
        TreeBuilder.create_simple_tree().children[0].children[0].children[0],
        "dummy_dir",
        url="dummy_url"
    )
    git.clone_or_pull_project(action)

    mock_git_repo.Repo.clone_from.assert_called_once_with("dummy_url", "dummy_dir", multi_options=[])

@mock.patch('gitlabber.git.git')
@mock.patch('gitlabber.git.is_git_repo')
def test_clone_repo_recursive(mock_is_git_repo, mock_git):
    """Test cloning with recursive flag."""
    mock_git_repo = MockGitRepo.create_mock_repo(is_git_repo=False)
    mock.patch('gitlabber.git.git', mock_git_repo).start()
    mock_is_git_repo.return_value = False

    node = Node(type="project", name="dummy_url", url="dummy_url")
    action = GitAction(node, "dummy_dir", recursive=True)
    git.clone_or_pull_project(action)

    mock_git_repo.Repo.clone_from.assert_called_once_with("dummy_url", "dummy_dir", multi_options=['--recursive'])

@mock.patch('gitlabber.git.git')
@mock.patch('gitlabber.git.is_git_repo')
def test_pull_repo_recursive(mock_is_git_repo, mock_git):
    """Test pulling with recursive flag."""
    mock_git_repo = MockGitRepo.create_mock_repo(is_git_repo=True)
    mock.patch('gitlabber.git.git', mock_git_repo).start()
    mock_is_git_repo.return_value = True

    node = Node(type="project", name="test")
    action = GitAction(node, "dummy_dir", recursive=True)
    git.clone_or_pull_project(action)
    
    mock_git_repo.Repo.assert_called_once_with("dummy_dir")
    mock_git_repo.Repo.return_value.remotes.origin.pull.assert_called_once()
    mock_git_repo.Repo.return_value.submodule_update.assert_called_once_with(recursive=True)

@mock.patch('gitlabber.git.git')
@mock.patch('gitlabber.git.is_git_repo')
def test_pull_repo_exception(mock_is_git_repo, mock_git):
    """Test that pull exceptions are properly handled."""
    mock_git_repo = MockGitRepo.create_mock_repo(
        is_git_repo=True,
        pull_side_effect=Exception('pull test exception')
    )
    mock_git_repo.exc = gitpython.exc
    mock.patch('gitlabber.git.git', mock_git_repo).start()
    mock_is_git_repo.return_value = True

    action = TreeBuilder.create_git_action(
        TreeBuilder.create_simple_tree().children[0].children[0].children[0],
        "dummy_dir",
        url="dummy_url"
    )
    
    with pytest.raises(GitlabberGitError):
        git.clone_or_pull_project(action)

    mock_git_repo.Repo.assert_called_once_with("dummy_dir")
    mock_git_repo.Repo.return_value.remotes.origin.pull.assert_called_once()
    
@mock.patch('gitlabber.git.git')
@mock.patch('gitlabber.git.is_git_repo')
def test_clone_repo_exception(mock_is_git_repo, mock_git):
    """Test that clone exceptions are properly handled."""
    mock_git_repo = MockGitRepo.create_mock_repo(is_git_repo=False)
    mock_git_repo.exc = gitpython.exc
    mock.patch('gitlabber.git.git', mock_git_repo).start()
    mock_is_git_repo.return_value = False

    # Create a GitCommandError to match actual exception handling
    clone_error = gitpython.exc.GitCommandError('clone', 'clone test exception')
    mock_git_repo.Repo.clone_from.side_effect = clone_error

    node = Node(type="project", name="dummy_url", url="dummy_url")
    action = GitAction(node, "dummy_dir")
    
    # The function should raise GitlabberGitError
    with pytest.raises(GitlabberGitError):
        git.clone_or_pull_project(action)
    
    mock_git_repo.Repo.clone_from.assert_called_once_with('dummy_url', 'dummy_dir', multi_options=[])

@mock.patch('gitlabber.git.git')
@mock.patch('gitlabber.git.is_git_repo')
def test_pull_repo_interrupt(mock_is_git_repo, mock_git):
    """Test handling of keyboard interrupt during pull."""
    mock_git_repo = MockGitRepo.create_mock_repo(
        is_git_repo=True,
        pull_side_effect=KeyboardInterrupt('pull test keyboard interrupt')
    )
    mock.patch('gitlabber.git.git', mock_git_repo).start()
    mock_is_git_repo.return_value = True

    node = Node(type="project", name="dummy_url", url="dummy_url")
    action = GitAction(node, "dummy_dir")
    
    with pytest.raises(SystemExit):
        git.clone_or_pull_project(action)

    mock_git_repo.Repo.assert_called_once_with("dummy_dir")
    mock_git_repo.Repo.return_value.remotes.origin.pull.assert_called_once()

@mock.patch('gitlabber.git.git')
@mock.patch('gitlabber.git.is_git_repo')
def test_clone_repo_interrupt(mock_is_git_repo, mock_git):
    """Test handling of keyboard interrupt during clone."""
    mock_git_repo = MockGitRepo.create_mock_repo(
        is_git_repo=False,
        clone_side_effect=KeyboardInterrupt('clone test keyboard interrupt')
    )
    mock.patch('gitlabber.git.git', mock_git_repo).start()
    mock_is_git_repo.return_value = False

    node = Node(type="project", name="dummy_url", url="dummy_url")
    action = GitAction(node, "dummy_dir")
    
    with pytest.raises(SystemExit):
        git.clone_or_pull_project(action)

    mock_git_repo.Repo.clone_from.assert_called_once_with("dummy_url", "dummy_dir", multi_options=[])


@mock.patch('gitlabber.git.git')
@mock.patch('gitlabber.git.is_git_repo')
def test_clone_repo_options_many_options(mock_is_git_repo, mock_git):
    """Test cloning with multiple git options."""
    mock_git_repo = MockGitRepo.create_mock_repo(is_git_repo=False)
    mock.patch('gitlabber.git.git', mock_git_repo).start()
    mock_is_git_repo.return_value = False

    node = Node(type="project", name="dummy_url", url="dummy_url")
    action = GitAction(node, "dummy_dir", git_options="--opt1=1,--opt2=2")
    git.clone_or_pull_project(action)

    mock_git_repo.Repo.clone_from.assert_called_once_with("dummy_url", "dummy_dir", multi_options=['--opt1=1','--opt2=2'])
    
    
@mock.patch('gitlabber.git.git')
@mock.patch('gitlabber.git.is_git_repo')
def test_clone_repo_options_with_recursive(mock_is_git_repo, mock_git):
    """Test cloning with recursive flag and git options."""
    mock_git_repo = MockGitRepo.create_mock_repo(is_git_repo=False)
    mock.patch('gitlabber.git.git', mock_git_repo).start()
    mock_is_git_repo.return_value = False

    node = Node(type="project", name="dummy_url", url="dummy_url")
    action = GitAction(node, "dummy_dir", recursive=True, git_options="--opt1=1,--opt2=2")
    git.clone_or_pull_project(action)

    mock_git_repo.Repo.clone_from.assert_called_once_with("dummy_url", "dummy_dir", multi_options=['--recursive','--opt1=1','--opt2=2'])