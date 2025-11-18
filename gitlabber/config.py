"""Configuration classes for gitlabber."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .auth import AuthProvider
from .method import CloneMethod
from .naming import FolderNaming


class GitlabberConfig(BaseModel):
    """Validated configuration for Gitlabber operations."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    url: str
    token: str
    method: CloneMethod
    naming: Optional[FolderNaming] = None
    archived: Optional[bool] = None
    includes: Optional[list[str]] = None
    excludes: Optional[list[str]] = None
    concurrency: int = Field(1, gt=0)
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

    @field_validator("includes", "excludes", mode="before")
    @classmethod
    def _ensure_str_list(cls, value):
        if value in (None, "", []):
            return None
        if isinstance(value, str):
            return [value]
        return [str(item) for item in value if str(item)]
