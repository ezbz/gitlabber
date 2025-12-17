
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

@mock.patch('gitlabber.git.git')
@mock.patch('gitlabber.git.is_git_repo')
def test_clone_repo_mirror(mock_is_git_repo, mock_git):
    """Test cloning with mirror flag creates bare repository."""
    mock_git_repo = MockGitRepo.create_mock_repo(is_git_repo=False)
    mock.patch('gitlabber.git.git', mock_git_repo).start()
    mock_is_git_repo.return_value = False

    node = Node(type="project", name="dummy_url", url="dummy_url")
    action = GitAction(node, "dummy_dir", mirror=True)
    git.clone_or_pull_project(action)

    mock_git_repo.Repo.clone_from.assert_called_once_with("dummy_url", "dummy_dir", multi_options=['--mirror'])

@mock.patch('gitlabber.git.git')
@mock.patch('gitlabber.git.is_git_repo')
def test_clone_repo_mirror_with_recursive(mock_is_git_repo, mock_git):
    """Test cloning with mirror and recursive flags."""
    mock_git_repo = MockGitRepo.create_mock_repo(is_git_repo=False)
    mock.patch('gitlabber.git.git', mock_git_repo).start()
    mock_is_git_repo.return_value = False

    node = Node(type="project", name="dummy_url", url="dummy_url")
    action = GitAction(node, "dummy_dir", recursive=True, mirror=True)
    git.clone_or_pull_project(action)

    mock_git_repo.Repo.clone_from.assert_called_once_with("dummy_url", "dummy_dir", multi_options=['--recursive', '--mirror'])

def test_pull_repo_mirror_uses_fetch():
    """Test that mirror repositories use fetch instead of pull."""
    mock_git_repo = MockGitRepo.create_mock_repo(is_git_repo=True)
    with mock.patch('gitlabber.git.git', mock_git_repo):
        with mock.patch('gitlabber.git.is_git_repo', return_value=True):
            node = Node(type="project", name="test")
            action = GitAction(node, "dummy_dir", mirror=True)
            git.clone_or_pull_project(action)
            
            mock_git_repo.Repo.assert_called_once_with("dummy_dir")
            mock_git_repo.Repo.return_value.remotes.origin.fetch.assert_called_once()
            mock_git_repo.Repo.return_value.remotes.origin.pull.assert_not_called()

@mock.patch('gitlabber.git.git')
@mock.patch('gitlabber.git.is_git_repo')
def test_clone_repo_use_fetch_normal_repo(mock_is_git_repo, mock_git):
    """Test that use_fetch creates normal repo (not bare) but uses fetch for updates."""
    mock_git_repo = MockGitRepo.create_mock_repo(is_git_repo=False)
    mock.patch('gitlabber.git.git', mock_git_repo).start()
    mock_is_git_repo.return_value = False

    node = Node(type="project", name="dummy_url", url="dummy_url")
    action = GitAction(node, "dummy_dir", use_fetch=True)
    git.clone_or_pull_project(action)

    # Should NOT include --mirror, just normal clone
    mock_git_repo.Repo.clone_from.assert_called_once_with("dummy_url", "dummy_dir", multi_options=[])

@mock.patch('gitlabber.git.git')
@mock.patch('gitlabber.git.is_git_repo')
def test_pull_repo_use_fetch(mock_is_git_repo, mock_git):
    """Test that use_fetch uses fetch instead of pull for updates."""
    mock_git_repo = MockGitRepo.create_mock_repo(is_git_repo=True)
    mock.patch('gitlabber.git.git', mock_git_repo).start()
    mock_is_git_repo.return_value = True

    node = Node(type="project", name="test")
    action = GitAction(node, "dummy_dir", use_fetch=True)
    git.clone_or_pull_project(action)
    
    mock_git_repo.Repo.assert_called_once_with("dummy_dir")
    mock_git_repo.Repo.return_value.remotes.origin.fetch.assert_called_once()
    mock_git_repo.Repo.return_value.remotes.origin.pull.assert_not_called()

def test_use_fetch_and_mirror_interaction():
    """Test comprehensive interaction between use_fetch and mirror flags.
    
    This test ensures:
    1. use_fetch alone: normal repo, uses fetch for updates
    2. mirror alone: bare repo, uses fetch for updates (mirror implies use_fetch)
    3. both flags: bare repo (mirror takes precedence), uses fetch for updates
    4. mirror=True, use_fetch=False: still uses fetch (mirror implies use_fetch)
    """
    # Test 1: use_fetch=True, mirror=False - normal repo, fetch for updates
    mock_git_repo = MockGitRepo.create_mock_repo(is_git_repo=False)
    with mock.patch('gitlabber.git.git', mock_git_repo):
        with mock.patch('gitlabber.git.is_git_repo', return_value=False):
            node = Node(type="project", name="test1", url="test1_url")
            action = GitAction(node, "test1_dir", use_fetch=True, mirror=False)
            git.clone_or_pull_project(action)
            
            # Should create normal repo (no --mirror)
            mock_git_repo.Repo.clone_from.assert_called_once_with("test1_url", "test1_dir", multi_options=[])
    
    # Test 2: use_fetch=False, mirror=True - bare repo, fetch for updates (mirror implies use_fetch)
    mock_git_repo = MockGitRepo.create_mock_repo(is_git_repo=False)
    with mock.patch('gitlabber.git.git', mock_git_repo):
        with mock.patch('gitlabber.git.is_git_repo', return_value=False):
            node2 = Node(type="project", name="test2", url="test2_url")
            action2 = GitAction(node2, "test2_dir", use_fetch=False, mirror=True)
            git.clone_or_pull_project(action2)
            
            # Should create bare repo (with --mirror)
            mock_git_repo.Repo.clone_from.assert_called_once_with("test2_url", "test2_dir", multi_options=['--mirror'])
    
    # Test 3: use_fetch=True, mirror=True - bare repo (mirror takes precedence), fetch for updates
    mock_git_repo = MockGitRepo.create_mock_repo(is_git_repo=False)
    with mock.patch('gitlabber.git.git', mock_git_repo):
        with mock.patch('gitlabber.git.is_git_repo', return_value=False):
            node3 = Node(type="project", name="test3", url="test3_url")
            action3 = GitAction(node3, "test3_dir", use_fetch=True, mirror=True)
            git.clone_or_pull_project(action3)
            
            # Should create bare repo (mirror takes precedence)
            mock_git_repo.Repo.clone_from.assert_called_once_with("test3_url", "test3_dir", multi_options=['--mirror'])
    
    # Test 4: Verify pull behavior - mirror=True should use fetch even if use_fetch=False
    mock_git_repo = MockGitRepo.create_mock_repo(is_git_repo=True)
    with mock.patch('gitlabber.git.git', mock_git_repo):
        with mock.patch('gitlabber.git.is_git_repo', return_value=True):
            node4 = Node(type="project", name="test4")
            action4 = GitAction(node4, "test4_dir", use_fetch=False, mirror=True)
            git.clone_or_pull_project(action4)

            # Mirror should imply use_fetch, so should use fetch, not pull
            mock_git_repo.Repo.assert_called_once_with("test4_dir")
            mock_git_repo.Repo.return_value.remotes.origin.fetch.assert_called_once()
            mock_git_repo.Repo.return_value.remotes.origin.pull.assert_not_called()


def test_git_action_collector_mirror_implies_use_fetch():
    """Test that GitActionCollector correctly implements mirror implies use_fetch logic.
    
    This ensures that when mirror=True, the collected GitAction has use_fetch=True
    even if use_fetch was originally False.
    """
    from gitlabber.git import GitActionCollector
    from anytree import Node
    
    # Create a simple tree with one project
    root = Node("root", type="root", root_path="")
    Node(type="project", name="test_project", 
         root_path="/test_project", url="test_url", parent=root)
    
    # Test: mirror=True, use_fetch=False - should result in use_fetch=True
    collector = GitActionCollector(
        dest="/tmp/test",
        recursive=False,
        use_fetch=False,  # Explicitly False
        mirror=True,      # But mirror is True
        hide_token=False,
        git_options=None
    )
    
    actions = collector.collect(root)
    
    assert len(actions) == 1
    action = actions[0]
    assert action.mirror is True
    # Mirror should imply use_fetch, so this should be True
    assert action.use_fetch is True, "mirror=True should imply use_fetch=True"
    
    # Test: mirror=True, use_fetch=True - should result in use_fetch=True
    collector2 = GitActionCollector(
        dest="/tmp/test",
        recursive=False,
        use_fetch=True,
        mirror=True,
        hide_token=False,
        git_options=None
    )
    
    actions2 = collector2.collect(root)
    assert len(actions2) == 1
    action2 = actions2[0]
    assert action2.mirror is True
    assert action2.use_fetch is True
    
    # Test: mirror=False, use_fetch=True - should result in use_fetch=True
    collector3 = GitActionCollector(
        dest="/tmp/test",
        recursive=False,
        use_fetch=True,
        mirror=False,
        hide_token=False,
        git_options=None
    )
    
    actions3 = collector3.collect(root)
    assert len(actions3) == 1
    action3 = actions3[0]
    assert action3.mirror is False
    assert action3.use_fetch is True
    
    # Test: mirror=False, use_fetch=False - should result in use_fetch=False
    collector4 = GitActionCollector(
        dest="/tmp/test",
        recursive=False,
        use_fetch=False,
        mirror=False,
        hide_token=False,
        git_options=None
    )
    
    actions4 = collector4.collect(root)
    assert len(actions4) == 1
    action4 = actions4[0]
    assert action4.mirror is False
    assert action4.use_fetch is False


@mock.patch('gitlabber.git.git')
@mock.patch('gitlabber.git.is_git_repo')
def test_all_flag_combinations_clone_behavior(mock_is_git_repo, mock_git):
    """Test all combinations of use_fetch and mirror flags for clone behavior.
    
    Verifies that:
    - Neither flag: normal clone, no special options
    - use_fetch only: normal clone, no --mirror
    - mirror only: bare clone with --mirror
    - both flags: bare clone with --mirror (mirror takes precedence)
    """
    test_cases = [
        # (use_fetch, mirror, expected_multi_options, description)
        (False, False, [], "Neither flag: normal clone"),
        (True, False, [], "use_fetch only: normal clone (no --mirror)"),
        (False, True, ['--mirror'], "mirror only: bare clone"),
        (True, True, ['--mirror'], "both flags: bare clone (mirror takes precedence)"),
    ]
    
    for use_fetch, mirror, expected_options, description in test_cases:
        mock_git_repo = MockGitRepo.create_mock_repo(is_git_repo=False)
        mock.patch('gitlabber.git.git', mock_git_repo).start()
        mock_is_git_repo.return_value = False
        
        node = Node(type="project", name=f"test_{use_fetch}_{mirror}", url="test_url")
        action = GitAction(node, f"test_dir_{use_fetch}_{mirror}", 
                         use_fetch=use_fetch, mirror=mirror)
        git.clone_or_pull_project(action)
        
        mock_git_repo.Repo.clone_from.assert_called_once_with(
            "test_url", 
            f"test_dir_{use_fetch}_{mirror}", 
            multi_options=expected_options
        )
        assert mock_git_repo.Repo.clone_from.call_args[1]['multi_options'] == expected_options, \
            f"Failed for {description}: expected {expected_options}, got {mock_git_repo.Repo.clone_from.call_args[1]['multi_options']}"


def test_all_flag_combinations_pull_behavior():
    """Test all combinations of use_fetch and mirror flags for pull/fetch behavior.
    
    Verifies that:
    - Neither flag: uses pull
    - use_fetch only: uses fetch
    - mirror only: uses fetch (mirror implies use_fetch)
    - both flags: uses fetch
    """
    test_cases = [
        # (use_fetch, mirror, should_use_fetch, description)
        (False, False, False, "Neither flag: should use pull"),
        (True, False, True, "use_fetch only: should use fetch"),
        (False, True, True, "mirror only: should use fetch (mirror implies use_fetch)"),
        (True, True, True, "both flags: should use fetch"),
    ]
    
    for use_fetch, mirror, should_use_fetch, description in test_cases:
        mock_git_repo = MockGitRepo.create_mock_repo(is_git_repo=True)
        with mock.patch('gitlabber.git.git', mock_git_repo):
            with mock.patch('gitlabber.git.is_git_repo', return_value=True):
                node = Node(type="project", name=f"test_{use_fetch}_{mirror}")
                action = GitAction(node, f"test_dir_{use_fetch}_{mirror}",
                                 use_fetch=use_fetch, mirror=mirror)
                git.clone_or_pull_project(action)
                
                if should_use_fetch:
                    mock_git_repo.Repo.return_value.remotes.origin.fetch.assert_called_once()
                    mock_git_repo.Repo.return_value.remotes.origin.pull.assert_not_called()
                else:
                    mock_git_repo.Repo.return_value.remotes.origin.pull.assert_called_once()
                    mock_git_repo.Repo.return_value.remotes.origin.fetch.assert_not_called()