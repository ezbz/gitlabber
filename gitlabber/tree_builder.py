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


class TreeFilter:
    """Apply include/exclude filters to a tree."""

    def __init__(
        self,
        includes: Optional[List[str]] = None,
        excludes: Optional[List[str]] = None,
    ):
        self.includes = includes or []
        self.excludes = excludes or []

    def apply(self, root: Node) -> None:
        for child in list(root.children):
            if not child.is_leaf:
                self.apply(child)
                if child.is_leaf and not self._should_keep(child):
                    child.parent = None
            else:
                if not self._should_keep(child):
                    child.parent = None

    def _should_keep(self, node: Node) -> bool:
        if self._is_excluded(node):
            return False
        if not self.includes:
            return True
        return self._is_included(node)

    def _is_included(self, node: Node) -> bool:
        return any(globre.match(include, node.root_path) for include in self.includes)

    def _is_excluded(self, node: Node) -> bool:
        return any(globre.match(exclude, node.root_path) for exclude in self.excludes)


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

