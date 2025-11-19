"""Main GitLab tree management and synchronization.

This module provides the GitlabTree class which orchestrates building
the project hierarchy from GitLab, filtering it, and synchronizing
repositories to the local filesystem.
"""

from typing import Optional, Union
from gitlab import Gitlab
from gitlab.exceptions import GitlabAuthenticationError
from anytree import Node, RenderTree
from anytree.exporter import DictExporter, JsonExporter
from .git import sync_tree
from .format import PrintFormat
from .method import CloneMethod
from .naming import FolderNaming
from .progress import ProgressBar
from .auth import AuthProvider, TokenAuthProvider
from .config import GitlabberConfig
from .exceptions import (
    GitlabberTreeError,
    GitlabberAPIError,
    GitlabberAuthenticationError as GitlabberAuthError,
    GitlabberGitError
)
from .tree_builder import GitlabTreeBuilder, TreeFilter
import logging
import os
import yaml

log = logging.getLogger(__name__)

class GitlabTree:
    def __init__(self, 
                 url: Optional[str] = None,
                 token: Optional[str] = None,
                 method: Optional[CloneMethod] = None,
                 naming: Optional[FolderNaming] = None,
                 archived: Optional[bool] = None,
                 includes: Optional[list[str]] = None,
                 excludes: Optional[list[str]] = None,
                 in_file: Optional[str] = None,
                 concurrency: int = 1,
                 recursive: bool = False,
                 disable_progress: bool = False,
                 include_shared: bool = True,
                 use_fetch: bool = False,
                 hide_token: bool = False,
                 user_projects: bool = False,
                 group_search: Optional[str] = None,
                 git_options: Optional[str] = None,
                 auth_provider: Optional[AuthProvider] = None,
                 fail_fast: bool = False,
                 config: Optional[GitlabberConfig] = None) -> None:
        """Initialize GitlabTree.
        
        Args:
            config: GitlabberConfig object (preferred method)
            url: GitLab instance URL (used if config not provided)
            token: Personal access token (used if config not provided)
            method: Clone method (SSH or HTTP) (used if config not provided)
            naming: Folder naming strategy (used if config not provided)
            archived: Whether to include archived projects (used if config not provided)
            includes: List of glob patterns to include (used if config not provided)
            excludes: List of glob patterns to exclude (used if config not provided)
            in_file: YAML file to load tree from (used if config not provided)
            concurrency: Number of concurrent git operations (used if config not provided)
            recursive: Whether to clone recursively (used if config not provided)
            disable_progress: Whether to disable progress bar (used if config not provided)
            include_shared: Whether to include shared projects (used if config not provided)
            use_fetch: Whether to use git fetch instead of pull (used if config not provided)
            hide_token: Whether to hide token in URLs (used if config not provided)
            user_projects: Whether to fetch only user projects (used if config not provided)
            group_search: Search term for filtering groups (used if config not provided)
            git_options: Additional git options as CSV string (used if config not provided)
            auth_provider: Authentication provider (used if config not provided)
            fail_fast: Whether to abort on the first discovery error
            config: Optional GitlabberConfig to provide settings
            
        Raises:
            GitlabberAuthenticationError: If authentication fails
            GitlabberAPIError: If GitLab client initialization fails
        """
        # Use config if provided, otherwise use individual parameters
        if config:
            url = config.url
            token = config.token
            method = config.method
            naming = config.naming
            archived = config.archived
            includes = config.includes
            excludes = config.excludes
            in_file = config.in_file
            concurrency = config.concurrency
            api_concurrency = config.api_concurrency
            api_rate_limit = config.api_rate_limit
            recursive = config.recursive
            disable_progress = config.disable_progress
            include_shared = config.include_shared
            use_fetch = config.use_fetch
            hide_token = config.hide_token
            user_projects = config.user_projects
            group_search = config.group_search
            git_options = config.git_options
            auth_provider = config.auth_provider
            fail_fast = config.fail_fast
        else:
            # Set defaults for api_concurrency and api_rate_limit when not using config
            api_concurrency = 5
            api_rate_limit = None
        
        if not url or not token or not method:
            raise GitlabberAPIError("url, token, and method are required (either via config or individual parameters)")
        
        self.includes = includes or []
        self.excludes = excludes or []
        self.url = url
        self.root = Node("", root_path="", url=url, type="root")
        
        # Use provided auth provider or default to token-based auth
        self.auth_provider = auth_provider or TokenAuthProvider(token)
        
        try:
            self.gitlab = Gitlab(url, private_token=token,
                               ssl_verify=GitlabTree.get_ca_path())
            
            # Configure connection pool size to match api_concurrency
            # This prevents "Connection pool is full" warnings when making concurrent requests
            # Set pool size to api_concurrency * 2 to provide headroom
            pool_size = max(api_concurrency * 2, 10)  # At least 10, or 2x concurrency
            if hasattr(self.gitlab, 'session'):
                # Recreate adapters with larger connection pool
                from requests.adapters import HTTPAdapter
                # Create new adapters with larger pool size
                https_adapter = HTTPAdapter(pool_connections=pool_size, pool_maxsize=pool_size)
                http_adapter = HTTPAdapter(pool_connections=pool_size, pool_maxsize=pool_size)
                # Mount the new adapters
                self.gitlab.session.mount('https://', https_adapter)
                self.gitlab.session.mount('http://', http_adapter)
                log.debug(f"Configured connection pool: pool_maxsize={pool_size}")
            
            # Authenticate using the provider
            self.auth_provider.authenticate(self.gitlab)
        except GitlabAuthenticationError as e:
            from .exceptions import format_error_with_suggestion
            error_msg, suggestion = format_error_with_suggestion(
                'api_auth',
                f"Failed to authenticate with GitLab at {url}: {str(e)}",
                {'url': url, 'token': '***' if token else None}
            )
            log.error(error_msg)
            raise GitlabberAuthError(error_msg, suggestion) from e
        except Exception as e:
            error_str = str(e).lower()
            error_type = 'api_503' if '503' in error_str or 'service unavailable' in error_str else None
            from .exceptions import format_error_with_suggestion
            error_msg, suggestion = format_error_with_suggestion(
                error_type or 'api_auth',
                f"Failed to initialize GitLab client for {url}: {str(e)}",
                {'url': url}
            )
            log.error(error_msg, exc_info=True)
            raise GitlabberAPIError(error_msg, suggestion) from e
            
        self.method = method
        self.naming = naming
        self.archived = archived
        self.in_file = in_file
        self.concurrency = concurrency
        self.api_concurrency = api_concurrency
        self.api_rate_limit = api_rate_limit
        self.recursive = recursive
        self.disable_progress = disable_progress
        self.progress = ProgressBar('* loading tree', disable_progress)
        self.token = token
        self.include_shared = include_shared
        self.use_fetch = use_fetch
        self.hide_token = hide_token
        self.user_projects = user_projects
        self.group_search = group_search
        self.git_options = git_options
        self.fail_fast = fail_fast

    def handle_error(self, message: str, exc: Optional[Exception] = None) -> None:
        """Handle an error according to fail_fast settings."""
        if self.fail_fast:
            raise GitlabberTreeError(message) from exc
        if exc:
            log.error(message, exc_info=True)
        else:
            log.error(message)

    @staticmethod
    def get_ca_path() -> Union[str, bool]:
        """Returns REQUESTS_CA_BUNDLE, CURL_CA_BUNDLE, or True"""
        return next(item for item in [os.getenv('REQUESTS_CA_BUNDLE', None), 
                                    os.getenv('CURL_CA_BUNDLE', None), 
                                    True]
                   if item is not None)

    def _builder(self) -> GitlabTreeBuilder:
        return GitlabTreeBuilder(
            self.gitlab,
            progress=self.progress,
            naming=self.naming,
            method=self.method,
            archived=self.archived,
            include_shared=self.include_shared,
            hide_token=self.hide_token,
            token=self.token,
            logger=log,
            error_handler=self.handle_error,
            api_concurrency=getattr(self, 'api_concurrency', 5),
            api_rate_limit=getattr(self, 'api_rate_limit', None),
        )

    def add_projects(self, parent, projects) -> None:
        """Expose builder project addition for testing/backwards compatibility."""
        self._builder().add_projects(parent, projects)

    def get_subgroups(self, group, parent) -> None:
        self._builder().get_subgroups(group, parent)

    def get_projects(self, group, parent) -> None:
        self._builder().get_projects(group, parent)

    def load_tree(self) -> None:
        """Load the tree structure from appropriate source."""
        builder = self._builder()
        try:
            if self.in_file:
                log.debug("Loading tree from file [%s]", self.in_file)
                self.root = builder.build_from_file(self.in_file)
            elif self.user_projects:
                log.debug(
                    "Loading user personal projects from gitlab server [%s]", self.url
                )
                self.root = builder.build_from_user_projects(self.url)
            else:
                log.debug("Loading projects tree from gitlab server [%s]", self.url)
                self.root = builder.build_from_gitlab(self.url, self.group_search)

            TreeFilter(self.includes, self.excludes).apply(self.root)
            log.debug("Fetched root node with [%d] projects", len(self.root.leaves))
        except Exception as e:
            message = f"Failed to load tree: {str(e)}"
            self.handle_error(message, e)

    def print_tree(self, format: PrintFormat = PrintFormat.TREE) -> None:
        """Print the tree in specified format.
        
        Args:
            format: Print format to use
            
        Raises:
            GitlabberTreeError: If printing fails
        """
        try:
            if format is PrintFormat.TREE:
                self.print_tree_native()
            elif format is PrintFormat.YAML:
                self.print_tree_yaml()
            elif format is PrintFormat.JSON:
                self.print_tree_json()
            else:
                error_msg = f"Invalid print format: {format}"
                log.error(error_msg)
                raise GitlabberTreeError(error_msg)
        except GitlabberTreeError:
            raise
        except Exception as e:
            error_msg = f"Failed to print tree: {str(e)}"
            log.error(error_msg, exc_info=True)
            raise GitlabberTreeError(error_msg) from e

    def print_tree_native(self) -> None:
        """Print tree in native format."""
        for pre, _, node in RenderTree(self.root):
            line = ""
            if node.is_root:
                line = f"{pre}root [{self.url}]"
            else:
                line = f"{pre}{node.name} [{node.root_path}]"
            print(line)

    def print_tree_yaml(self) -> None:
        """Print tree in YAML format."""
        dct = DictExporter().export(self.root)
        print(yaml.dump(dct, default_flow_style=False))

    def print_tree_json(self) -> None:
        """Print tree in JSON format."""
        exporter = JsonExporter(indent=2, sort_keys=True)
        print(exporter.export(self.root))

    def sync_tree(self, dest: str) -> None:
        """Sync the tree to destination.
        
        Args:
            dest: Destination path
            
        Raises:
            GitlabberGitError: If git operations fail
            GitlabberTreeError: If sync fails
        """
        try:
            log.debug("Going to clone/pull [%s] groups and [%s] projects",
                     len(self.root.descendants) - len(self.root.leaves), len(self.root.leaves))
            sync_tree(self.root, dest, concurrency=self.concurrency,
                     disable_progress=self.disable_progress, recursive=self.recursive,
                     use_fetch=self.use_fetch, hide_token=self.hide_token,
                     git_options=self.git_options)
        except GitlabberGitError:
            # Re-raise git errors as-is
            raise
        except Exception as e:
            error_msg = f"Failed to sync tree to {dest}: {str(e)}"
            log.error(error_msg, exc_info=True)
            raise GitlabberTreeError(error_msg) from e

    def is_empty(self) -> bool:
        """Check if the tree is empty.
        
        Returns:
            True if tree is empty, False otherwise
        """
        return self.root.height < 1
