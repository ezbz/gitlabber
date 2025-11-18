"""Configuration classes for gitlabber."""

from __future__ import annotations

from typing import Optional

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)
from pydantic_settings import BaseSettings

from .auth import AuthProvider
from .method import CloneMethod
from .naming import FolderNaming


class GitlabberSettings(BaseSettings):
    """Application settings sourced from environment variables."""

    model_config = ConfigDict(env_prefix="", case_sensitive=False, extra="ignore")

    token: Optional[str] = Field(
        default=None, validation_alias=AliasChoices("GITLAB_TOKEN")
    )
    url: Optional[str] = Field(
        default=None, validation_alias=AliasChoices("GITLAB_URL")
    )
    method: Optional[CloneMethod] = Field(
        default=None, validation_alias=AliasChoices("GITLABBER_CLONE_METHOD")
    )
    naming: Optional[FolderNaming] = Field(
        default=None, validation_alias=AliasChoices("GITLABBER_FOLDER_NAMING")
    )
    includes: Optional[list[str]] = Field(
        default=None, validation_alias=AliasChoices("GITLABBER_INCLUDE")
    )
    excludes: Optional[list[str]] = Field(
        default=None, validation_alias=AliasChoices("GITLABBER_EXCLUDE")
    )
    concurrency: Optional[int] = Field(
        default=None, validation_alias=AliasChoices("GITLABBER_GIT_CONCURRENCY")
    )
    api_concurrency: Optional[int] = Field(
        default=None, validation_alias=AliasChoices("GITLABBER_API_CONCURRENCY")
    )
    api_rate_limit: Optional[int] = Field(
        default=None, validation_alias=AliasChoices("GITLABBER_API_RATE_LIMIT")
    )

    @field_validator("includes", "excludes", mode="before")
    @classmethod
    def _split_csv(cls, value):
        if value in (None, "", []):
            return None
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


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
    api_concurrency: int = Field(5, ge=1, le=20)
    api_rate_limit: Optional[int] = Field(None, ge=1)
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
