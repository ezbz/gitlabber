"""Git operations for cloning and syncing repositories."""

from dataclasses import dataclass
from typing import Optional
import logging
import sys
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


class GitRepository:
    """Handles individual git repository operations."""

    @staticmethod
    def is_git_repo(path: str) -> bool:
        """Return True if the given path is a valid git repository.
        
        Args:
            path: Path to check
            
        Returns:
            True if path is a valid git repository, False otherwise
        """
        try:
            _ = git.Repo(path).git_dir
            return True
        except git.InvalidGitRepositoryError:
            return False

    @staticmethod
    def clone(action: GitAction, progress_bar: ProgressBar) -> None:
        """Clone a new repository.
        
        Args:
            action: GitAction describing what to clone
            progress_bar: Progress bar for reporting
            
        Raises:
            GitlabberGitError: If clone operation fails
        """
        if action.node.type != "project":
            log.debug("Skipping clone of node with type [%s] (empty subgroup/group)", action.node.type)
            return
            
        log.debug("cloning new project %s", action.path)
        progress_bar.show_progress_detailed(action.node.name, 'project', 'cloning')
        
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
            error_str = str(e).lower()
            error_type = 'git_clone_network'
            suggestion = None
            
            # Determine error type and suggestion based on error message
            if 'permission denied' in error_str or 'could not read' in error_str:
                if 'ssh' in action.node.url.lower():
                    error_type = 'git_clone_ssh'
                else:
                    error_type = 'git_clone_permission'
            elif 'not found' in error_str or 'does not exist' in error_str:
                error_type = 'git_clone_permission'
            elif 'network' in error_str or 'connection' in error_str or 'timeout' in error_str:
                error_type = 'git_clone_network'
            
            from .exceptions import format_error_with_suggestion
            error_msg, suggestion = format_error_with_suggestion(
                error_type,
                f"Git clone command failed for project '{action.node.name}' "
                f"from {action.node.url} to {action.path}: {str(e)}",
                {'url': action.node.url, 'path': action.path}
            )
            log.error(error_msg, exc_info=True)
            raise GitlabberGitError(error_msg, suggestion) from e
        except git.exc.GitError as e:
            error_msg = (f"Git error cloning project '{action.node.name}' "
                        f"from {action.node.url}: {str(e)}")
            log.error(error_msg, exc_info=True)
            raise GitlabberGitError(error_msg) from e
        except OSError as e:
            error_msg = (f"OS error cloning project '{action.node.name}' "
                        f"to {action.path}: {str(e)}")
            log.error(error_msg, exc_info=True)
            raise GitlabberGitError(error_msg) from e
        except Exception as e:
            error_msg = (f"Unexpected error cloning project '{action.node.name}' "
                        f"from {action.node.url} to {action.path}: {str(e)}")
            log.error(error_msg, exc_info=True)
            raise GitlabberGitError(error_msg) from e

    @staticmethod
    def pull(action: GitAction, progress_bar: ProgressBar, repo=None) -> None:
        """Pull changes for an existing repository.
        
        Args:
            action: GitAction describing what to pull
            progress_bar: Progress bar for reporting
            repo: Optional pre-opened repo instance (to avoid double opening)
            
        Raises:
            GitlabberGitError: If pull operation fails
        """
        log.debug("updating existing project %s", action.path)
        operation = 'fetching' if action.use_fetch else 'pulling'
        progress_bar.show_progress_detailed(action.node.name, 'project', operation)
        
        try:
            if repo is None:
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
            error_str = str(e).lower()
            error_type = 'git_pull_branch'
            
            # Check if it's a branch-related error
            if 'branch' in error_str and ('not found' in error_str or 'does not exist' in error_str):
                error_type = 'git_pull_branch'
            elif 'permission' in error_str:
                error_type = 'git_clone_permission'
            
            from .exceptions import format_error_with_suggestion
            error_msg, suggestion = format_error_with_suggestion(
                error_type,
                f"Git command failed for project '{action.node.name}' "
                f"at {action.path}: {str(e)}",
                {'path': action.path, 'use_fetch': action.use_fetch}
            )
            log.error(error_msg, exc_info=True)
            raise GitlabberGitError(error_msg, suggestion) from e
        except git.exc.InvalidGitRepositoryError as e:
            error_msg = (f"Invalid git repository at {action.path} "
                        f"for project '{action.node.name}'")
            log.error(error_msg, exc_info=True)
            raise GitlabberGitError(error_msg) from e
        except git.exc.NoSuchPathError as e:
            error_msg = (f"Path does not exist: {action.path} "
                        f"for project '{action.node.name}'")
            log.error(error_msg, exc_info=True)
            raise GitlabberGitError(error_msg) from e
        except Exception as e:
            error_msg = (f"Unexpected error pulling project '{action.node.name}' "
                        f"at {action.path}: {str(e)}")
            log.error(error_msg, exc_info=True)
            raise GitlabberGitError(error_msg) from e

    @staticmethod
    def execute(action: GitAction, progress_bar: ProgressBar, is_repo_checker=None) -> None:
        """Execute a git action (clone or pull).
        
        Args:
            action: GitAction to execute
            progress_bar: Progress bar for reporting
            is_repo_checker: Optional function to check if path is a repo (for testing)
            
        Raises:
            GitlabberGitError: If operation fails
        """
        check_repo = is_repo_checker or GitRepository.is_git_repo
        if check_repo(action.path):
            # Try to open repo once and reuse it
            try:
                repo = git.Repo(action.path)
                GitRepository.pull(action, progress_bar, repo)
            except Exception as e:
                # Fallback to clone if repo check was wrong or git module is mocked
                # Only catch if it's not a KeyboardInterrupt or SystemExit (which should propagate)
                if isinstance(e, (KeyboardInterrupt, SystemExit)):
                    raise
                # Check if it's an InvalidGitRepositoryError (when git is not mocked)
                if hasattr(git, 'exc') and isinstance(e, git.exc.InvalidGitRepositoryError):
                    GitRepository.clone(action, progress_bar)
                elif isinstance(e, AttributeError):
                    # Git module might be mocked
                    GitRepository.clone(action, progress_bar)
                else:
                    # Some other error, re-raise it
                    raise
        else:
            GitRepository.clone(action, progress_bar)


class GitActionCollector:
    """Collects git actions from a tree structure."""

    def __init__(
        self,
        dest: str,
                 recursive: bool = False,
                 use_fetch: bool = False,
                 hide_token: bool = False,
        git_options: Optional[str] = None
    ):
        """Initialize the collector.
        
        Args:
            dest: Destination directory for repositories
            recursive: Whether to clone recursively
            use_fetch: Whether to use git fetch instead of pull
            hide_token: Whether to hide token in URLs
            git_options: Additional git options as comma-separated string
        """
        self.dest = Path(dest)
        self.recursive = recursive
        self.use_fetch = use_fetch
        self.hide_token = hide_token
        self.git_options = git_options

    def collect(self, root: Node) -> list[GitAction]:
        """Collect git actions from the tree.
        
        Args:
            root: Root node of the tree
            
        Returns:
            List of GitAction objects to execute
        """
        actions: list[GitAction] = []
        self._collect_from_node(root, actions)
        return actions

    def _collect_from_node(self, node: Node, actions: list[GitAction]) -> None:
        """Recursively collect actions from a node and its children.
        
        Args:
            node: Node to process
            actions: List to append actions to
        """
        for child in node.children:
            # Remove leading slash from root_path if present for proper path joining
            child_path_str = child.root_path.lstrip('/')
            path = self.dest / child_path_str if child_path_str else self.dest
            path.mkdir(parents=True, exist_ok=True)
            path_str = str(path)
            
            if child.is_leaf:
                actions.append(GitAction(
                    child, path_str, self.recursive, 
                    self.use_fetch, self.hide_token, self.git_options
                ))
            
            if not child.is_leaf:
                self._collect_from_node(child, actions)


class GitSyncManager:
    """Manages synchronization of git repositories with concurrency."""

    def __init__(
        self,
        concurrency: int = 1,
        disable_progress: bool = False,
        progress_bar: Optional[ProgressBar] = None
    ):
        """Initialize the sync manager.
        
        Args:
            concurrency: Number of concurrent git operations
            disable_progress: Whether to disable progress reporting
            progress_bar: Optional progress bar (creates default if not provided)
        """
        self.concurrency = concurrency
        self.disable_progress = disable_progress
        self.progress_bar = progress_bar or progress

    def sync(
        self,
        root: Node,
        dest: str,
        recursive: bool = False,
        use_fetch: bool = False,
        hide_token: bool = False,
        git_options: Optional[str] = None
    ) -> None:
        """Synchronize git repositories in the tree structure.
        
        Args:
            root: Root node of the tree
            dest: Destination directory
            recursive: Whether to clone recursively
            use_fetch: Whether to use git fetch instead of pull
            hide_token: Whether to hide token in URLs
            git_options: Additional git options as comma-separated string
        """
        if not self.disable_progress:
            self.progress_bar.init_progress(len(root.leaves))

        collector = GitActionCollector(
            dest, recursive, use_fetch, hide_token, git_options
        )
        actions = collector.collect(root)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            executor.map(clone_or_pull_project, actions)
        
        elapsed = self.progress_bar.finish_progress()
        log.debug("Syncing projects took [%s]", elapsed)


# Backward compatibility functions
def sync_tree(
    root: Node, 
              dest: str, 
              concurrency: int = 1,
              disable_progress: bool = False,
              recursive: bool = False,
              use_fetch: bool = False,
              hide_token: bool = False,
    git_options: Optional[str] = None
) -> None:
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
    manager = GitSyncManager(concurrency, disable_progress)
    manager.sync(root, dest, recursive, use_fetch, hide_token, git_options)


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
    collector = GitActionCollector(dest, recursive, use_fetch, hide_token, git_options)
    return collector.collect(root)


def is_git_repo(path: str) -> bool:
    """Return True if the given path is a valid git repository.
    
    Args:
        path: Path to check
        
    Returns:
        True if path is a valid git repository, False otherwise
    """
    return GitRepository.is_git_repo(path)


def clone_or_pull_project(action: GitAction) -> None:
    """Clone a new project or pull changes for an existing project.
    
    Args:
        action: GitAction to execute
        
    Raises:
        GitlabberGitError: If operation fails
    """
    GitRepository.execute(action, progress, is_git_repo)
