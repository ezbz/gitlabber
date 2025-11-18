"""Helpers for building and filtering the GitLab tree."""

from __future__ import annotations

from pathlib import Path
import logging
from typing import Callable, List, Optional

import globre
import yaml
from anytree import Node
from anytree.importer import DictImporter
from gitlab.exceptions import GitlabGetError, GitlabListError

from .exceptions import GitlabberTreeError
from .method import CloneMethod
from .naming import FolderNaming
from .progress import ProgressBar


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
        groups = self.gitlab.groups.list(
            as_list=False,
            archived=self.archived,
            get_all=True,
            search=group_search,
        )
        self.progress.init_progress(len(groups))
        for group in groups:
            try:
                if group.parent_id is None:
                    group_id = (
                        group.name
                        if self.naming == FolderNaming.NAME
                        else group.path
                    )
                    node = self._make_node("group", group_id, root, group.web_url)
                    self.progress.show_progress(node.name, "group")
                    self.get_subgroups(group, node)
                    self.get_projects(group, node)
            except Exception as exc:  # pragma: no cover
                self._handle_error(
                    f"Error processing group {getattr(group, 'name', 'unknown')}: {exc}",
                    exc,
                )
                continue
        self.progress.finish_progress()
        return root

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
                project_url = (
                    project.ssh_url_to_repo
                    if self.method is CloneMethod.SSH
                    else project.http_url_to_repo
                )
                if self.token and self.method is CloneMethod.HTTP:
                    if not self.hide_token:
                        project_url = project_url.replace(
                            "://", f"://gitlab-token:{self.token}@"
                        )
                        self.log.debug("Generated URL: %s", project_url)
                    else:
                        self.log.debug("Hiding token from project url: %s", project_url)
                node = self._make_node("project", project_id, parent, project_url)
                self.progress.show_progress(node.name, "project")
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
            projects = group.projects.list(
                archived=self.archived, with_shared=self.include_shared, get_all=True
            )
            self.progress.update_progress_length(len(projects))
            self.add_projects(parent, projects)

            if self.include_shared and hasattr(group, "shared_projects"):
                shared_projects = group.shared_projects.list(get_all=True)
                self.progress.update_progress_length(len(shared_projects))
                self.add_projects(parent, shared_projects)
        except GitlabListError as error:
            self._handle_error(
                f"Error getting projects on {getattr(group, 'name', 'unknown')} id: "
                f"[{getattr(group, 'id', 'unknown')}] error message: [{error.error_message}]",
                error,
            )

    def get_subgroups(self, group, parent: Node) -> None:
        try:
            subgroups = group.subgroups.list(as_list=False, get_all=True)
            self.progress.update_progress_length(len(subgroups))
            for subgroup_def in subgroups:
                try:
                    subgroup = self.gitlab.groups.get(subgroup_def.id)
                    subgroup_id = (
                        subgroup.name
                        if self.naming == FolderNaming.NAME
                        else subgroup.path
                    )
                    node = self._make_node(
                        "subgroup", subgroup_id, parent, subgroup.web_url
                    )
                    self.progress.show_progress(node.name, "group")
                    self.get_subgroups(subgroup, node)
                    self.get_projects(subgroup, node)
                except GitlabGetError as error:
                    if error.response_code == 404:
                        self._handle_error(
                            f"{error.response_code} error while getting subgroup with name: "
                            f"{getattr(group, 'name', 'unknown')} [id: {getattr(group, 'id', 'unknown')}]. "
                            f"Check your permissions as you may not have access to it. Message: {error.error_message}",
                            error,
                        )
                    else:
                        self._handle_error(
                            f"Error getting subgroup: {error.error_message}", error
                        )
                    continue
        except GitlabListError as error:
            if error.response_code == 404:
                self._handle_error(
                    f"{error.response_code} error while listing subgroup with name: "
                    f"{getattr(group, 'name', 'unknown')} [id: {getattr(group, 'id', 'unknown')}]. "
                    f"Check your permissions as you may not have access to it. Message: {error.error_message}",
                    error,
                )
            else:
                self._handle_error(
                    f"Failed to get subgroups for group {getattr(group, 'name', 'unknown')}: {error.error_message}",
                    error,
                )

