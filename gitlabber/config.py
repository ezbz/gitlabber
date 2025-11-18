"""Configuration classes for gitlabber."""

from dataclasses import dataclass
from typing import Optional
from .method import CloneMethod
from .naming import FolderNaming
from .auth import AuthProvider


@dataclass
class GitlabberConfig:
    """Configuration for Gitlabber operations.
    
    Attributes:
        url: GitLab instance URL
        token: Personal access token
        method: Clone method (SSH or HTTP)
        naming: Folder naming strategy
        archived: Whether to include archived projects (None = include all)
        includes: List of glob patterns to include
        excludes: List of glob patterns to exclude
        concurrency: Number of concurrent git operations
        recursive: Whether to clone recursively
        disable_progress: Whether to disable progress bar
        include_shared: Whether to include shared projects
        use_fetch: Whether to use git fetch instead of pull
        hide_token: Whether to hide token in URLs
        user_projects: Whether to fetch only user projects
        group_search: Search term for filtering groups
        git_options: Additional git options as comma-separated string
        auth_provider: Authentication provider
        in_file: YAML file to load tree from (optional)
    """
    url: str
    token: str
    method: CloneMethod
    naming: Optional[FolderNaming] = None
    archived: Optional[bool] = None
    includes: Optional[list[str]] = None
    excludes: Optional[list[str]] = None
    concurrency: int = 1
    recursive: bool = False
    disable_progress: bool = False
    include_shared: bool = True
    use_fetch: bool = False
    hide_token: bool = False
    user_projects: bool = False
    group_search: Optional[str] = None
    git_options: Optional[str] = None
    fail_fast: bool = False
    auth_provider: Optional[AuthProvider] = None
    in_file: Optional[str] = None

