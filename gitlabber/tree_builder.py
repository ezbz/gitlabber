"""Helpers for building and filtering the GitLab tree."""

from __future__ import annotations

from pathlib import Path
import concurrent.futures
import logging
from typing import Any, Callable, List, Optional

import globre
import yaml
from anytree import Node
from anytree.importer import DictImporter
from gitlab.exceptions import GitlabGetError, GitlabListError

from .exceptions import GitlabberTreeError
from .method import CloneMethod
from .naming import FolderNaming
from .progress import ProgressBar
from .rate_limiter import RateLimitedExecutor
from .url_builder import build_project_url


# Functional predicate builders
def create_pattern_matcher(patterns: List[str]) -> Callable[[str], bool]:
    """Create a pure function that matches a path against glob patterns.
    
    Args:
        patterns: List of glob patterns to match against
        
    Returns:
        A function that takes a path and returns True if it matches any pattern
    """
    if not patterns:
        return lambda _: False
    
    compiled_patterns = patterns
    
    def matches(path: str) -> bool:
        return any(globre.match(pattern, path) for pattern in compiled_patterns)
    
    return matches


def create_include_predicate(includes: Optional[List[str]]) -> Callable[[Node], bool]:
    """Create a predicate function that checks if a node should be included.
    
    Args:
        includes: List of include patterns (None or empty means include all)
        
    Returns:
        A function that takes a Node and returns True if it should be included
    """
    if not includes:
        return lambda _: True
    
    matcher = create_pattern_matcher(includes)
    return lambda node: matcher(node.root_path)


def create_exclude_predicate(excludes: Optional[List[str]]) -> Callable[[Node], bool]:
    """Create a predicate function that checks if a node should be excluded.
    
    Args:
        excludes: List of exclude patterns
        
    Returns:
        A function that takes a Node and returns True if it should be excluded
    """
    if not excludes:
        return lambda _: False
    
    matcher = create_pattern_matcher(excludes)
    return lambda node: matcher(node.root_path)


def compose_predicates(
    include_pred: Callable[[Node], bool],
    exclude_pred: Callable[[Node], bool]
) -> Callable[[Node], bool]:
    """Compose include and exclude predicates into a single filter predicate.
    
    Args:
        include_pred: Predicate for inclusion check
        exclude_pred: Predicate for exclusion check
        
    Returns:
        A function that returns True if node should be kept (included and not excluded)
    """
    def should_keep(node: Node) -> bool:
        if exclude_pred(node):
            return False
        return include_pred(node)
    
    return should_keep


def filter_tree_functional(
    root: Node,
    should_keep: Callable[[Node], bool]
) -> None:
    """Filter a tree in-place using a functional predicate.
    
    This function traverses the tree and removes nodes that don't match
    the predicate. It processes children first (post-order traversal) to
    ensure parent nodes are evaluated after their children.
    
    Args:
        root: Root node of the tree to filter
        should_keep: Predicate function that determines if a node should be kept
    """
    def process_node(node: Node) -> None:
        # Process children first (post-order traversal)
        for child in list(node.children):
            if not child.is_leaf:
                process_node(child)
                # After processing children, check if this node should be kept
                # (it might be a leaf now if all children were removed)
                if child.is_leaf and not should_keep(child):
                    child.parent = None
            else:
                # Leaf node - check if it should be kept
                if not should_keep(child):
                    child.parent = None
    
    process_node(root)


class TreeFilter:
    """Apply include/exclude filters to a tree using a functional approach."""

    def __init__(
        self,
        includes: Optional[List[str]] = None,
        excludes: Optional[List[str]] = None,
    ):
        """Initialize the filter with include/exclude patterns.
        
        Args:
            includes: List of glob patterns to include (None/empty = include all)
            excludes: List of glob patterns to exclude
        """
        self.includes = includes or []
        self.excludes = excludes or []
        
        # Build functional predicates
        include_pred = create_include_predicate(self.includes)
        exclude_pred = create_exclude_predicate(self.excludes)
        self._should_keep = compose_predicates(include_pred, exclude_pred)

    def apply(self, root: Node) -> None:
        """Apply the filter to the tree, removing nodes that don't match.
        
        Args:
            root: Root node of the tree to filter
        """
        filter_tree_functional(root, self._should_keep)


class GitlabTreeBuilder:
    """Builds the tree structure from different sources."""

    def __init__(
        self,
        gitlab,
        *,
        progress: ProgressBar,
        naming: Optional[FolderNaming],
        method: CloneMethod,
        archived: Optional[bool],
        include_shared: bool,
        hide_token: bool,
        token: str,
        logger: Optional[logging.Logger] = None,
        error_handler: Optional[Callable[[str, Optional[Exception]], None]] = None,
        api_concurrency: int = 5,
        api_rate_limit: Optional[int] = None,
    ):
        self.gitlab = gitlab
        self.progress = progress
        self.naming = naming or FolderNaming.NAME
        self.method = method
        self.archived = archived
        self.include_shared = include_shared
        self.hide_token = hide_token
        self.token = token
        self.log = logger or logging.getLogger(__name__)
        self.error_handler = error_handler
        self.api_concurrency = api_concurrency
        self.rate_limiter = RateLimitedExecutor(
            max_requests_per_hour=api_rate_limit or 2000
        )

    def _handle_error(self, message: str, exc: Optional[Exception]) -> None:
        if self.error_handler:
            self.error_handler(message, exc)
        else:
            if exc:
                self.log.error(message, exc_info=True)
            else:
                self.log.error(message)

    def build_from_gitlab(
        self, base_url: str, group_search: Optional[str]
    ) -> Node:
        root = Node("", root_path="", url=base_url, type="root")
        
        # Rate limit the initial groups.list() call
        self.rate_limiter.acquire()
        groups = self.gitlab.groups.list(
            as_list=False,
            archived=self.archived,
            get_all=True,
            search=group_search,
        )
        
        # Filter to only top-level groups (parent_id is None)
        top_level_groups = [g for g in groups if g.parent_id is None]
        self.progress.init_progress(len(top_level_groups))
        
        # Process groups in parallel
        if self.api_concurrency > 1 and len(top_level_groups) > 1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.api_concurrency) as executor:
                futures = {
                    executor.submit(self._process_group_with_rate_limit, group, root): group
                    for group in top_level_groups
                }
                for future in concurrent.futures.as_completed(futures):
                    try:
                        future.result()
                    except Exception as exc:  # pragma: no cover
                        group = futures[future]
                        self._handle_error(
                            f"Error processing group {getattr(group, 'name', 'unknown')}: {exc}",
                            exc,
                        )
        else:
            # Sequential processing for single group or concurrency=1
            for group in top_level_groups:
                try:
                    self._process_group(group, root)
                except Exception as exc:  # pragma: no cover
                    self._handle_error(
                        f"Error processing group {getattr(group, 'name', 'unknown')}: {exc}",
                        exc,
                    )
                    continue
        
        self.progress.finish_progress()
        return root
    
    def _process_group_with_rate_limit(self, group, root: Node) -> None:
        """Process a group with rate limiting applied to API calls.
        
        This is a wrapper around _process_group that ensures rate limiting
        is applied to all API calls made during group processing.
        
        Args:
            group: GitLab group object
            root: Root node of the tree
        """
        self._process_group(group, root)
    
    def _process_group(self, group, root: Node) -> None:
        """Process a single group: create node and fetch subgroups/projects.
        
        Args:
            group: GitLab group object
            root: Root node of the tree
        """
        group_id = (
            group.name
            if self.naming == FolderNaming.NAME
            else group.path
        )
        node = self._make_node("group", group_id, root, group.web_url)
        self.progress.show_progress_detailed(node.name, "group", "processing")
        
        # Fetch subgroups and projects concurrently
        if self.api_concurrency > 1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                subgroup_future = executor.submit(self.get_subgroups, group, node)
                project_future = executor.submit(self.get_projects, group, node)
                subgroup_future.result()
                project_future.result()
        else:
            # Sequential for api_concurrency=1
            self.get_subgroups(group, node)
            self.get_projects(group, node)

    def build_from_file(self, path: str) -> Node:
        file_path = Path(path)
        if not file_path.exists():
            raise GitlabberTreeError(f"Tree file does not exist: {path}")

        try:
            with file_path.open("r") as stream:
                data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            raise GitlabberTreeError(f"Failed to parse YAML file {path}: {exc}") from exc

        if data is None:
            raise GitlabberTreeError(f"Tree file {path} is empty or invalid.")

        return DictImporter().import_(data)

    def build_from_user_projects(self, base_url: str) -> Node:
        root = Node("", root_path="", url=base_url, type="root")
        user = self.gitlab.users.get(self.gitlab.user.id)
        username = user.username
        projects = user.projects.list(
            as_list=False, archived=self.archived, get_all=True
        )
        self.progress.init_progress(len(projects))
        personal_root = self._make_node(
            "group",
            f"{username}-personal-projects",
            root,
            url=f"{base_url}/users/{username}/projects",
        )
        self.add_projects(personal_root, projects)
        return root

    def _root_path(self, node: Node) -> str:
        return "/".join(str(n.name) for n in node.path)

    def _make_node(self, type_: str, name: str, parent: Node, url: str) -> Node:
        node = Node(name=name, parent=parent, url=url, type=type_)
        node.root_path = self._root_path(node)
        return node

    def add_projects(self, parent: Node, projects) -> None:
        for project in projects:
            try:
                project_id = (
                    project.name
                    if self.naming == FolderNaming.NAME
                    else project.path
                )
                project_url = build_project_url(
                    http_url=project.http_url_to_repo,
                    ssh_url=project.ssh_url_to_repo,
                    method=self.method,
                    token=self.token,
                    hide_token=self.hide_token,
                    logger=self.log,
                )
                node = self._make_node("project", project_id, parent, project_url)
                self.progress.show_progress_detailed(node.name, "project", "adding")
            except AttributeError as exc:
                self._handle_error(
                    f"Failed to add project '{getattr(project, 'name', 'unknown')}': missing attribute - {exc}",
                    exc,
                )
                continue
            except Exception as exc:  # pragma: no cover
                self._handle_error(
                    f"Failed to add project '{getattr(project, 'name', 'unknown')}': {exc}",
                    exc,
                )
                continue

    def get_projects(self, group, parent: Node) -> None:
        try:
            self.rate_limiter.acquire()
            projects = group.projects.list(
                archived=self.archived, with_shared=self.include_shared, get_all=True
            )
            self.progress.update_progress_length(len(projects))
            self.add_projects(parent, projects)

            if self.include_shared and hasattr(group, "shared_projects"):
                self.rate_limiter.acquire()
                shared_projects = group.shared_projects.list(get_all=True)
                self.progress.update_progress_length(len(shared_projects))
                self.add_projects(parent, shared_projects)
        except GitlabListError as error:
            from .exceptions import format_error_with_suggestion
            error_type = 'api_permission'
            if error.response_code == 404:
                error_type = 'api_404'
            elif error.response_code == 503:
                error_type = 'api_503'
            error_msg, suggestion = format_error_with_suggestion(
                error_type,
                f"Error getting projects on {getattr(group, 'name', 'unknown')} id: "
                f"[{getattr(group, 'id', 'unknown')}] error message: [{error.error_message}]",
                {'group_name': getattr(group, 'name', 'unknown'), 'response_code': error.response_code}
            )
            self._handle_error(error_msg, error)

    def get_subgroups(self, group, parent: Node) -> None:
        """Get subgroups for a group, fetching details concurrently when multiple subgroups exist.
        
        Args:
            group: GitLab group object
            parent: Parent node in the tree
        """
        try:
            self.rate_limiter.acquire()
            subgroups = group.subgroups.list(as_list=False, get_all=True)
            self.progress.update_progress_length(len(subgroups))
            
            if not subgroups:
                return
            
            # Fetch all subgroup details concurrently
            if self.api_concurrency > 1 and len(subgroups) > 1:
                # Fetch subgroup details in parallel
                with concurrent.futures.ThreadPoolExecutor(max_workers=min(self.api_concurrency, len(subgroups))) as executor:
                    # Map futures to indices to preserve order
                    future_to_index = {
                        executor.submit(self._fetch_subgroup_detail, subgroup_def): idx
                        for idx, subgroup_def in enumerate(subgroups)
                    }
                    
                    # Store results in list to preserve order
                    fetched_subgroups = [None] * len(subgroups)
                    for future in concurrent.futures.as_completed(future_to_index):
                        idx = future_to_index[future]
                        try:
                            subgroup = future.result()
                            if subgroup:
                                fetched_subgroups[idx] = subgroup
                        except Exception as exc:  # pragma: no cover
                            subgroup_def = subgroups[idx]
                            self._handle_error(
                                f"Error fetching subgroup detail for {getattr(subgroup_def, 'name', 'unknown')}: {exc}",
                                exc,
                            )
                    
                    # Process fetched subgroups concurrently
                    # This parallelizes the recursive processing of each subgroup
                    if len(fetched_subgroups) > 1:
                        with concurrent.futures.ThreadPoolExecutor(max_workers=min(self.api_concurrency, len(fetched_subgroups))) as executor:
                            futures = []
                            for subgroup in fetched_subgroups:
                                if subgroup:
                                    futures.append(executor.submit(self._process_subgroup, subgroup, parent))
                            # Wait for all to complete
                            for future in concurrent.futures.as_completed(futures):
                                try:
                                    future.result()
                                except Exception as exc:  # pragma: no cover
                                    self._handle_error(
                                        f"Error processing subgroup: {exc}",
                                        exc,
                                    )
                    else:
                        # Single subgroup - process sequentially
                        for subgroup in fetched_subgroups:
                            if subgroup:
                                self._process_subgroup(subgroup, parent)
            else:
                # Sequential processing for single subgroup or api_concurrency=1
                for subgroup_def in subgroups:
                    try:
                        self.rate_limiter.acquire()
                        subgroup = self.gitlab.groups.get(subgroup_def.id)
                        self._process_subgroup(subgroup, parent)
                    except GitlabGetError as error:
                        from .exceptions import format_error_with_suggestion
                        if error.response_code == 404:
                            error_msg, suggestion = format_error_with_suggestion(
                                'api_404',
                                f"{error.response_code} error while getting subgroup with name: "
                                f"{getattr(group, 'name', 'unknown')} [id: {getattr(group, 'id', 'unknown')}]. "
                                f"Message: {error.error_message}",
                                {'group_name': getattr(group, 'name', 'unknown')}
                            )
                            self._handle_error(error_msg, error)
                        else:
                            error_msg, suggestion = format_error_with_suggestion(
                                'api_permission',
                                f"Error getting subgroup: {error.error_message}",
                                {'response_code': error.response_code}
                            )
                            self._handle_error(error_msg, error)
                        continue
        except GitlabListError as error:
            from .exceptions import format_error_with_suggestion
            if error.response_code == 404:
                error_msg, suggestion = format_error_with_suggestion(
                    'api_404',
                    f"{error.response_code} error while listing subgroup with name: "
                    f"{getattr(group, 'name', 'unknown')} [id: {getattr(group, 'id', 'unknown')}]. "
                    f"Message: {error.error_message}",
                    {'group_name': getattr(group, 'name', 'unknown')}
                )
                self._handle_error(error_msg, error)
            else:
                error_msg, suggestion = format_error_with_suggestion(
                    'api_permission',
                    f"Failed to get subgroups for group {getattr(group, 'name', 'unknown')}: {error.error_message}",
                    {'response_code': error.response_code}
                )
                self._handle_error(error_msg, error)
    
    def _fetch_subgroup_detail(self, subgroup_def) -> Optional[Any]:
        """Fetch subgroup detail with rate limiting.
        
        Args:
            subgroup_def: Subgroup definition from list
            
        Returns:
            Subgroup object or None if error
        """
        try:
            self.rate_limiter.acquire()
            return self.gitlab.groups.get(subgroup_def.id)
        except GitlabGetError as error:
            from .exceptions import format_error_with_suggestion
            if error.response_code == 404:
                error_msg, suggestion = format_error_with_suggestion(
                    'api_404',
                    f"{error.response_code} error while getting subgroup with id: "
                    f"{getattr(subgroup_def, 'id', 'unknown')}. "
                    f"Message: {error.error_message}",
                    {'subgroup_id': getattr(subgroup_def, 'id', 'unknown')}
                )
                self._handle_error(error_msg, error)
            else:
                error_msg, suggestion = format_error_with_suggestion(
                    'api_permission',
                    f"Error getting subgroup detail: {error.error_message}",
                    {'response_code': error.response_code}
                )
                self._handle_error(error_msg, error)
            return None
        except Exception as exc:  # pragma: no cover
            self._handle_error(
                f"Unexpected error fetching subgroup detail: {exc}",
                exc,
            )
            return None
    
    def _process_subgroup(self, subgroup, parent: Node) -> None:
        """Process a fetched subgroup: create node and recursively fetch children.
        
        Args:
            subgroup: GitLab subgroup object (fully fetched)
            parent: Parent node in the tree
        """
        subgroup_id = (
            subgroup.name
            if self.naming == FolderNaming.NAME
            else subgroup.path
        )
        node = self._make_node(
            "subgroup", subgroup_id, parent, subgroup.web_url
        )
        self.progress.show_progress_detailed(node.name, "subgroup", "processing")
        # Recursively process subgroups and projects
        if self.api_concurrency > 1:
            # Fetch subgroups and projects concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                subgroup_future = executor.submit(self.get_subgroups, subgroup, node)
                project_future = executor.submit(self.get_projects, subgroup, node)
                subgroup_future.result()
                project_future.result()
        else:
            # Sequential for api_concurrency=1
            self.get_subgroups(subgroup, node)
            self.get_projects(subgroup, node)

