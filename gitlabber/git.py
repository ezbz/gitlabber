from dataclasses import dataclass
from typing import Optional
import logging
import os
import sys
import subprocess
import git
from pathlib import Path
from anytree import Node
from .progress import ProgressBar
from .exceptions import GitlabberGitError
import concurrent.futures

log = logging.getLogger(__name__)

progress = ProgressBar('* syncing projects')


@dataclass(slots=True)
class GitAction:
    """Description of a single git action to perform for a tree leaf."""

    node: Node
    path: str
    recursive: bool = False
    use_fetch: bool = False
    hide_token: bool = False
    git_options: Optional[str] = None


def sync_tree(root: Node, 
              dest: str, 
              concurrency: int = 1,
              disable_progress: bool = False,
              recursive: bool = False,
              use_fetch: bool = False,
              hide_token: bool = False,
              git_options: Optional[str] = None) -> None:
    """
    Synchronizes the git repositories in the tree structure
    
    Args:
        root: Root node of the tree
        dest: Destination directory
        concurrency: Number of concurrent git operations
        disable_progress: Whether to disable progress reporting
        recursive: Whether to clone recursively
        use_fetch: Whether to use git fetch instead of pull
        hide_token: Whether to hide token in URLs
        git_options: Additional git options as comma-separated string
    """
    if not disable_progress:
        progress.init_progress(len(root.leaves))

    actions = get_git_actions(root, dest, recursive, use_fetch, hide_token, git_options)

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        executor.map(clone_or_pull_project, actions)
    
    elapsed = progress.finish_progress()
    log.debug("Syncing projects took [%s]", elapsed)


def get_git_actions(
    root: Node,
    dest: str,
    recursive: bool,
    use_fetch: bool,
    hide_token: bool,
    git_options: Optional[str] = None
) -> list[GitAction]:
    """Get list of git actions to perform for the tree.
    
    Args:
        root: Root node of the tree
        dest: Destination directory
        recursive: Whether to clone recursively
        use_fetch: Whether to use git fetch instead of pull
        hide_token: Whether to hide token in URLs
        git_options: Additional git options as comma-separated string
        
    Returns:
        List of GitAction objects to execute
    """
    actions: list[GitAction] = []
    dest_path = Path(dest)
    for child in root.children:
        # Remove leading slash from root_path if present for proper path joining
        child_path_str = child.root_path.lstrip('/')
        path = dest_path / child_path_str if child_path_str else dest_path
        path.mkdir(parents=True, exist_ok=True)
        path_str = str(path)
        if child.is_leaf:
            actions.append(GitAction(child, path_str, recursive, use_fetch, hide_token, git_options))            
        if not child.is_leaf:
            actions.extend(get_git_actions(child, dest, recursive, use_fetch, hide_token, git_options))
    return actions


def is_git_repo(path: str) -> bool:
    """Return True if the given path is a valid git repository."""
    try:
        _ = git.Repo(path).git_dir
        return True
    except git.InvalidGitRepositoryError:
        return False


def clone_or_pull_project(action: GitAction) -> None:
    """Clone a new project or pull changes for an existing project."""
    if is_git_repo(action.path):
        '''
        Update existing project
        '''
        log.debug("updating existing project %s", action.path)
        progress.show_progress(action.node.name, 'pull')
        
        try:
            repo = git.Repo(action.path)
            if not action.use_fetch:
                repo.remotes.origin.pull()
            else:
                repo.remotes.origin.fetch()
            if action.recursive: 
                repo.submodule_update(recursive=True)
        except KeyboardInterrupt:
            log.critical("User interrupted")
            sys.exit(0)
        except git.exc.GitCommandError as e:
            error_msg = f"Git command failed for project '{action.node.name}' at {action.path}: {str(e)}"
            log.error(error_msg, exc_info=True)
            raise GitlabberGitError(error_msg) from e
        except git.exc.InvalidGitRepositoryError as e:
            error_msg = f"Invalid git repository at {action.path} for project '{action.node.name}'"
            log.error(error_msg, exc_info=True)
            raise GitlabberGitError(error_msg) from e
        except git.exc.NoSuchPathError as e:
            error_msg = f"Path does not exist: {action.path} for project '{action.node.name}'"
            log.error(error_msg, exc_info=True)
            raise GitlabberGitError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error pulling project '{action.node.name}' at {action.path}: {str(e)}"
            log.error(error_msg, exc_info=True)
            raise GitlabberGitError(error_msg) from e
    else:
        '''
        Clone new project
        '''
        if action.node.type != "project":
            log.debug("Skipping clone of node with type [%s] (empty subgroup/group)", action.node.type)
            return
        log.debug("cloning new project %s", action.path)
        progress.show_progress(action.node.name, 'clone')
        multi_options: list[str] = []
        if action.recursive:
            multi_options.append('--recursive')
        if action.use_fetch:
            multi_options.append('--mirror')
        if action.git_options:
            multi_options += action.git_options.split(',')
        try:
            git.Repo.clone_from(action.node.url, action.path, multi_options=multi_options)
        except KeyboardInterrupt:
            log.critical("User interrupted")
            sys.exit(0)
        except git.exc.GitCommandError as e:
            error_msg = f"Git clone command failed for project '{action.node.name}' from {action.node.url} to {action.path}: {str(e)}"
            log.error(error_msg, exc_info=True)
            raise GitlabberGitError(error_msg) from e
        except git.exc.GitError as e:
            error_msg = f"Git error cloning project '{action.node.name}' from {action.node.url}: {str(e)}"
            log.error(error_msg, exc_info=True)
            raise GitlabberGitError(error_msg) from e
        except OSError as e:
            error_msg = f"OS error cloning project '{action.node.name}' to {action.path}: {str(e)}"
            log.error(error_msg, exc_info=True)
            raise GitlabberGitError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error cloning project '{action.node.name}' from {action.node.url} to {action.path}: {str(e)}"
            log.error(error_msg, exc_info=True)
            raise GitlabberGitError(error_msg) from e

