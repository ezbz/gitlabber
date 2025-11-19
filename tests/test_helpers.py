"""Comprehensive test utilities and helpers for gitlabber tests."""
from typing import Any, Optional
from unittest import mock
from anytree import Node
from gitlabber.method import CloneMethod
from gitlabber.git import GitAction
from gitlabber.config import GitlabberConfig, GitlabberSettings


class MockGitRepo:
    """Helper class for creating and managing mocked Git repositories."""

    @staticmethod
    def create_mock_repo(
        path: str = "dummy_dir",
        is_git_repo: bool = True,
        pull_side_effect: Optional[Exception] = None,
        clone_side_effect: Optional[Exception] = None,
    ) -> mock.Mock:
        """Create a mocked GitPython Repo instance.
        
        Args:
            path: Repository path
            is_git_repo: Whether the path should be treated as a git repo
            pull_side_effect: Optional exception to raise on pull
            clone_side_effect: Optional exception to raise on clone
            
        Returns:
            Mocked git module
        """
        mock_git = mock.Mock()
        mock_repo_instance = mock.Mock()
        mock_repo_instance.remotes.origin.pull = mock.Mock()
        if pull_side_effect:
            mock_repo_instance.remotes.origin.pull.side_effect = pull_side_effect
        mock_repo_instance.submodule_update = mock.Mock()
        
        mock_git.Repo.return_value = mock_repo_instance
        mock_git.Repo.clone_from.return_value = mock_repo_instance
        if clone_side_effect:
            mock_git.Repo.clone_from.side_effect = clone_side_effect
        
        # Mock is_git_repo behavior
        if is_git_repo:
            mock_git.Repo.side_effect = lambda p: mock_repo_instance if p == path else mock.Mock()
        else:
            mock_git.Repo.side_effect = lambda p: mock.Mock()
            
        return mock_git


class MockGitlabAPI:
    """Helper class for creating mocked GitLab API responses."""

    @staticmethod
    def create_mock_project(
        id: int = 1,
        name: str = "project",
        path: str = "project",
        url: str = "http://gitlab.example.com/project.git",
        ssh_url: Optional[str] = None,
        http_url: Optional[str] = None,
        archived: bool = False,
        shared: bool = False,
    ) -> mock.Mock:
        """Create a mocked GitLab Project object.
        
        Args:
            id: Project ID
            name: Project name
            path: Project path
            url: Project URL
            ssh_url: SSH URL (defaults to url if not provided)
            http_url: HTTP URL (defaults to url if not provided)
            archived: Whether project is archived
            shared: Whether project is shared
            
        Returns:
            Mocked Project object
        """
        mock_project = mock.Mock()
        mock_project.id = id
        mock_project.name = name
        mock_project.path = path
        mock_project.url = url
        mock_project.web_url = url
        mock_project.ssh_url_to_repo = ssh_url or url
        mock_project.http_url_to_repo = http_url or url
        mock_project.archived = archived
        mock_project.shared = shared
        return mock_project

    @staticmethod
    def create_mock_group(
        id: int = 1,
        name: str = "group",
        path: str = "group",
        url: str = "http://gitlab.example.com/group",
        parent_id: Optional[int] = None,
        archived: bool = False,
        projects: Optional[list[mock.Mock]] = None,
        subgroups: Optional[list[mock.Mock]] = None,
    ) -> mock.Mock:
        """Create a mocked GitLab Group object.
        
        Args:
            id: Group ID
            name: Group name
            path: Group path
            url: Group URL
            parent_id: Parent group ID
            archived: Whether group is archived
            projects: List of mock projects
            subgroups: List of mock subgroups
            
        Returns:
            Mocked Group object
        """
        mock_group = mock.Mock()
        mock_group.id = id
        mock_group.name = name
        mock_group.path = path
        mock_group.url = url
        mock_group.web_url = url
        mock_group.parent_id = parent_id
        mock_group.archived = archived
        
        # Create listable mock for projects and subgroups
        if projects:
            mock_group.projects = MockListable(*projects)
        else:
            mock_group.projects = MockListable()
            
        if subgroups:
            mock_group.subgroups = MockListable(*subgroups)
        else:
            mock_group.subgroups = MockListable()
            
        return mock_group


class MockListable:
    """Mock listable object that mimics GitLab API list() behavior."""

    def __init__(self, *items: Any):
        self.items = list(items)
        self.get_result = None
        self.list_result = None

    def list(
        self,
        as_list: bool = False,
        archived: Optional[bool] = None,
        with_shared: bool = True,
        get_all: bool = True,
        search: Optional[str] = None,
    ) -> list:
        """Mock list() method that filters items based on criteria."""
        filtered = self.items
        
        if archived is not None:
            filtered = [
                item for item in filtered
                if getattr(item, "archived", False) == archived
            ]
            
        if not with_shared:
            filtered = [
                item for item in filtered
                if not getattr(item, "shared", False)
            ]
            
        if search:
            filtered = [
                item for item in filtered
                if search.lower() in getattr(item, "name", "").lower()
            ]
            
        return filtered

    def get(self, id: Any) -> Optional[Any]:
        """Mock get() method that retrieves item by ID."""
        if self.get_result is not None:
            return self.get_result
        return next((item for item in self.items if getattr(item, "id", None) == id), None)


class TestConfigBuilder:
    """Builder class for creating test configurations."""

    @staticmethod
    def create_config(**overrides: Any) -> GitlabberConfig:
        """Create a GitlabberConfig with test defaults.
        
        Args:
            **overrides: Configuration values to override defaults
            
        Returns:
            GitlabberConfig instance
        """
        defaults = {
            "token": "test_token",
            "url": "http://gitlab.example.com",
            "method": CloneMethod.SSH,
            "naming": "name",
            "includes": None,
            "excludes": None,
            "concurrency": 1,
            "api_concurrency": 5,
            "api_rate_limit": None,
            "hide_token": True,
        }
        defaults.update(overrides)
        return GitlabberConfig(**defaults)

    @staticmethod
    def create_settings(**overrides: Any) -> mock.Mock:
        """Create a mocked GitlabberSettings with test defaults.
        
        Args:
            **overrides: Settings values to override defaults
            
        Returns:
            Mocked GitlabberSettings instance
        """
        defaults = {
            "token": None,
            "url": None,
            "method": None,
            "naming": None,
            "includes": None,
            "excludes": None,
            "concurrency": None,
            "api_concurrency": None,
            "api_rate_limit": None,
        }
        defaults.update(overrides)
        return mock.Mock(spec=GitlabberSettings, **defaults)


class TreeBuilder:
    """Helper class for building test tree structures."""

    @staticmethod
    def create_simple_tree(
        root_name: str = "root",
        group_name: str = "group",
        subgroup_name: str = "subgroup",
        project_name: str = "project",
    ) -> Node:
        """Create a simple test tree structure.
        
        Args:
            root_name: Root node name
            group_name: Group node name
            subgroup_name: Subgroup node name
            project_name: Project node name
            
        Returns:
            Root Node of the tree
        """
        root = Node(type="root", name=root_name)
        group = Node(
            type="group",
            name=group_name,
            root_path=f"/{group_name}",
            parent=root,
        )
        subgroup = Node(
            type="subgroup",
            name=subgroup_name,
            root_path=f"/{group_name}/{subgroup_name}",
            parent=group,
        )
        Node(
            type="project",
            name=project_name,
            root_path=f"/{group_name}/{subgroup_name}/{project_name}",
            parent=subgroup,
        )
        return root

    @staticmethod
    def create_git_action(
        node: Node,
        path: str,
        url: Optional[str] = None,
        recursive: bool = False,
        git_options: Optional[str] = None,
    ) -> GitAction:
        """Create a GitAction from a node.
        
        Args:
            node: Tree node
            path: Destination path
            url: Repository URL (sets node.url if provided)
            recursive: Whether to clone recursively
            git_options: Additional git options
            
        Returns:
            GitAction instance
        """
        if url:
            node.url = url
        return GitAction(
            node=node,
            path=path,
            recursive=recursive,
            git_options=git_options,
        )


class AssertionHelpers:
    """Helper methods for common test assertions."""

    @staticmethod
    def assert_tree_structure(
        root: Node,
        expected_depth: int,
        expected_children_counts: Optional[list[int]] = None,
    ) -> None:
        """Assert that a tree has the expected structure.
        
        Args:
            root: Root node of the tree
            expected_depth: Expected tree depth
            expected_children_counts: Optional list of expected child counts at each level
        """
        assert root.height == expected_depth, f"Expected depth {expected_depth}, got {root.height}"
        
        if expected_children_counts:
            current_level = [root]
            for i, expected_count in enumerate(expected_children_counts):
                actual_count = len(current_level[0].children) if current_level else 0
                assert actual_count == expected_count, (
                    f"Level {i}: expected {expected_count} children, got {actual_count}"
                )
                if current_level:
                    current_level = [
                        child for node in current_level for child in node.children
                    ]

    @staticmethod
    def assert_node_attributes(
        node: Node,
        **expected_attrs: Any,
    ) -> None:
        """Assert that a node has the expected attributes.
        
        Args:
            node: Node to check
            **expected_attrs: Expected attribute values
        """
        for attr_name, expected_value in expected_attrs.items():
            actual_value = getattr(node, attr_name, None)
            assert actual_value == expected_value, (
                f"Node {node.name}: expected {attr_name}={expected_value}, "
                f"got {actual_value}"
            )


def patch_module(module_path: str, **attributes: Any) -> mock.patch:
    """Create a patch for a module with specified attributes.
    
    Args:
        module_path: Path to the module to patch
        **attributes: Attributes to set on the mocked module
        
    Returns:
        Mock patch context manager
    """
    return mock.patch(module_path, **attributes)


def create_context_manager(enter_value: Any, exit_value: Any = None) -> mock.Mock:
    """Create a mock context manager.
    
    Args:
        enter_value: Value to return from __enter__
        exit_value: Value to return from __exit__
        
    Returns:
        Mock context manager
    """
    cm = mock.Mock()
    cm.__enter__ = mock.Mock(return_value=enter_value)
    cm.__exit__ = mock.Mock(return_value=exit_value)
    return cm

