"""Utilities for building repository clone URLs."""

from __future__ import annotations

import logging
from typing import Optional

from .method import CloneMethod

LogLike = logging.Logger


def _inject_token(url: str, token: str) -> str:
    """Inject a masked token into the provided HTTP URL."""
    return url.replace("://", f"://gitlab-token:{token}@")


def select_project_url(
    *,
    http_url: str,
    ssh_url: str,
    method: CloneMethod,
) -> str:
    """Select the appropriate base URL for a project based on clone method."""
    if method is CloneMethod.SSH:
        return ssh_url
    return http_url


def build_project_url(
    *,
    http_url: str,
    ssh_url: str,
    method: CloneMethod,
    token: Optional[str],
    hide_token: bool,
    logger: Optional[LogLike] = None,
) -> str:
    """Return the final project URL (with optional token injection)."""

    log = logger or logging.getLogger(__name__)
    base_url = select_project_url(http_url=http_url, ssh_url=ssh_url, method=method)

    if method is CloneMethod.HTTP and token:
        if hide_token:
            log.debug("Hiding token from project url: %s", base_url)
            return base_url

        tokenized_url = _inject_token(base_url, token)
        log.debug("Generated URL: %s", tokenized_url)
        return tokenized_url

    return base_url

