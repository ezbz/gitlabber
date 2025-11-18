from typing import Optional, Any, Union
from gitlab import Gitlab
from gitlab.exceptions import GitlabGetError, GitlabListError, GitlabAuthenticationError
from gitlab.v4.objects import Group, Project, User
from anytree import Node, RenderTree
from anytree.exporter import DictExporter, JsonExporter
from anytree.importer import DictImporter
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
import yaml
import globre
import logging
import os
from pathlib import Path

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
            # Authenticate using the provider
            self.auth_provider.authenticate(self.gitlab)
        except GitlabAuthenticationError as e:
            error_msg = f"Failed to authenticate with GitLab at {url}: {str(e)}"
            log.error(error_msg)
            raise GitlabberAuthError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to initialize GitLab client for {url}: {str(e)}"
            log.error(error_msg, exc_info=True)
            raise GitlabberAPIError(error_msg) from e
            
        self.method = method
        self.naming = naming
        self.archived = archived
        self.in_file = in_file
        self.concurrency = concurrency
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

    def is_included(self, node: Node) -> bool:
        """Check if a node should be included based on include patterns.
        
        Args:
            node: Node to check
            
        Returns:
            True if node should be included, False otherwise
        """
        if not self.includes:
            return True
            
        for include in self.includes:
            log.debug("Checking requested include: %s with path: %s, match %s",
                     include, node.root_path, globre.match(include, node.root_path))
            if globre.match(include, node.root_path):
                return True
        return False

    def is_excluded(self, node: Node) -> bool:
        """Check if a node should be excluded based on exclude patterns.
        
        Args:
            node: Node to check
            
        Returns:
            True if node should be excluded, False otherwise
        """
        if not self.excludes:
            return False
            
        for exclude in self.excludes:
            log.debug("Checking requested exclude: %s with path: %s, match %s",
                     exclude, node.root_path, globre.match(exclude, node.root_path))
            if globre.match(exclude, node.root_path):
                return True
        return False

    def filter_tree(self, parent: Node) -> None:
        """Filter the tree based on include/exclude patterns.
        
        Args:
            parent: Parent node to filter
        """
        for child in parent.children:
            if not child.is_leaf:
                self.filter_tree(child)
                if child.is_leaf:
                    if not self.is_included(child) or self.is_excluded(child):
                        child.parent = None
            else:
                if not self.is_included(child) or self.is_excluded(child):
                    child.parent = None

    def root_path(self, node: Node) -> str:
        """Get the root path for a node.
        
        Args:
            node: Node to get path for
            
        Returns:
            Path string
        """
        return "/".join(str(n.name) for n in node.path)

    def make_node(self, type: str, name: str, parent: Node, url: str) -> Node:
        """Create a new node in the tree.
        
        Args:
            type: Node type
            name: Node name
            parent: Parent node
            url: Node URL
            
        Returns:
            Created node
        """
        node = Node(name=name, parent=parent, url=url, type=type)
        node.root_path = self.root_path(node)
        return node

    def add_projects(self, parent: Node, projects: list[Project]) -> None:
        """Add projects to the tree.
        
        Args:
            parent: Parent node
            projects: List of projects to add
            
        Raises:
            GitlabberAPIError: If project addition fails
        """
        for project in projects:
            try:
                project_id = project.name if self.naming == FolderNaming.NAME else project.path
                project_url = project.ssh_url_to_repo if self.method is CloneMethod.SSH else project.http_url_to_repo
                if self.token is not None and self.method is CloneMethod.HTTP:
                    if not self.hide_token:
                        project_url = project_url.replace('://', f'://gitlab-token:{self.token}@')
                        log.debug("Generated URL: %s", project_url)
                    else:
                        log.debug("Hiding token from project url: %s", project_url)
                node = self.make_node("project", project_id, parent, url=project_url)
                self.progress.show_progress(node.name, 'project')
            except AttributeError as e:
                error_msg = f"Failed to add project '{project.name if hasattr(project, 'name') else 'unknown'}': missing required attribute - {str(e)}"
                log.error(error_msg)
                # Continue with other projects rather than failing completely
                continue
            except Exception as e:
                error_msg = f"Failed to add project '{project.name if hasattr(project, 'name') else 'unknown'}': {str(e)}"
                log.error(error_msg, exc_info=True)
                # Continue with other projects rather than failing completely
                continue

    def get_projects(self, group: Group, parent: Node) -> None:
        """Get projects for a group.
        
        Args:
            group: Group to get projects for
            parent: Parent node
        """
        try:
            projects = group.projects.list(archived=self.archived, with_shared=self.include_shared, get_all=True)
            self.progress.update_progress_length(len(projects))
            self.add_projects(parent, projects)
            
            if self.include_shared and hasattr(group, 'shared_projects'):
                shared_projects = group.shared_projects.list(get_all=True)
                self.progress.update_progress_length(len(shared_projects))
                self.add_projects(parent, shared_projects)
        except GitlabListError as error:
            message = (f"Error getting projects on {group.name} id: [{group.id}] "
                       f"error message: [{error.error_message}]")
            self.handle_error(message, error)

    def get_subgroups(self, group: Group, parent: Node) -> None:
        """Get subgroups for a group.
        
        Args:
            group: Group to get subgroups for
            parent: Parent node
        """
        try:
            subgroups = group.subgroups.list(as_list=False, get_all=True)
            self.progress.update_progress_length(len(subgroups))
            for subgroup_def in subgroups:
                try:
                    subgroup = self.gitlab.groups.get(subgroup_def.id)
                    subgroup_id = subgroup.name if self.naming == FolderNaming.NAME else subgroup.path
                    node = self.make_node("subgroup", subgroup_id, parent, url=subgroup.web_url)
                    self.progress.show_progress(node.name, 'group')
                    self.get_subgroups(subgroup, node)
                    self.get_projects(subgroup, node)
                except GitlabGetError as error:
                    if error.response_code == 404:
                        message = (f"{error.response_code} error while getting subgroup with name: "
                                   f"{group.name} [id: {group.id}]. Check your permissions as you "
                                   f"may not have access to it. Message: {error.error_message}")
                    else:
                        message = f"Error getting subgroup: {error.error_message}"
                    self.handle_error(message, error)
                    continue
        except GitlabListError as error:
            if error.response_code == 404:
                message = (f"{error.response_code} error while listing subgroup with name: "
                           f"{group.name} [id: {group.id}]. Check your permissions as you may not "
                           f"have access to it. Message: {error.error_message}")
            else:
                message = f"Failed to get subgroups for group {group.name}: {error.error_message}"
            self.handle_error(message, error)

    def load_gitlab_tree(self) -> None:
        """Load the GitLab tree structure."""
        log.debug("Starting group search with archived: %s search term: %s", self.archived, self.group_search)
                    
        try:
            groups = self.gitlab.groups.list(as_list=False, archived=self.archived, get_all=True, search=self.group_search)
            self.progress.init_progress(len(groups))
            for group in groups:
                try:
                    if group.parent_id is None:
                        group_id = group.name if self.naming == FolderNaming.NAME else group.path
                        node = self.make_node("group", group_id, self.root, url=group.web_url)
                        self.progress.show_progress(node.name, 'group')
                        self.get_subgroups(group, node)
                        self.get_projects(group, node)
                except Exception as e:
                    message = f"Error processing group {group.name}: {str(e)}"
                    self.handle_error(message, e)
                    continue

            elapsed = self.progress.finish_progress()
            log.debug("Loading projects tree from gitlab took [%s]", elapsed)
        except Exception as e:
            message = f"Failed to load GitLab tree: {str(e)}"
            self.handle_error(message, e)

    def load_file_tree(self) -> None:
        """Load tree structure from a YAML file."""
        try:
            file_path = Path(self.in_file)
            if not file_path.exists():
                error_msg = f"Tree file does not exist: {self.in_file}"
                log.error(error_msg)
                raise GitlabberTreeError(error_msg)
            with file_path.open('r') as stream:
                dct = yaml.safe_load(stream)
                self.root = DictImporter().import_(dct)
        except GitlabberTreeError:
            raise
        except FileNotFoundError as e:
            error_msg = f"Tree file not found: {self.in_file}"
            log.error(error_msg)
            raise GitlabberTreeError(error_msg) from e
        except yaml.YAMLError as e:
            error_msg = f"Failed to parse YAML file {self.in_file}: {str(e)}"
            log.error(error_msg)
            raise GitlabberTreeError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to load tree from file {self.in_file}: {str(e)}"
            log.error(error_msg, exc_info=True)
            raise GitlabberTreeError(error_msg) from e

    def load_user_tree(self) -> None:
        """Load user's personal projects."""
        log.debug("Starting user project search with archived: %s", self.archived)
        try:
            user = self.gitlab.users.get(self.gitlab.user.id)
            username = user.username
            projects = user.projects.list(as_list=False, archived=self.archived, get_all=True)
            self.progress.init_progress(len(projects))
            root = self.make_node("group", f"{username}-personal-projects", self.root, url=f"{self.url}/users/{username}/projects")
            self.add_projects(root, projects)
        except Exception as e:
            message = f"Failed to load user projects: {str(e)}"
            self.handle_error(message, e)

    def load_tree(self) -> None:
        """Load the tree structure from appropriate source."""
        try:
            if self.in_file:
                log.debug("Loading tree from file [%s]", self.in_file)
                self.load_file_tree()
            elif self.user_projects:
                log.debug("Loading user personal projects from gitlab server [%s]", self.url)
                self.load_user_tree()
            else:
                log.debug("Loading projects tree from gitlab server [%s]", self.url)
                self.load_gitlab_tree()

            log.debug("Fetched root node with [%d] projects", len(self.root.leaves))
            self.filter_tree(self.root)
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
