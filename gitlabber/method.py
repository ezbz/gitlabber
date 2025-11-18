"""Git clone method enumeration.

This module defines the available methods for cloning Git repositories
from GitLab (SSH or HTTP/HTTPS).
"""

import enum


class CloneMethod(enum.StrEnum):
    """Git transport method for cloning repositories.
    
    Attributes:
        SSH: Clone using SSH protocol (requires SSH keys)
        HTTP: Clone using HTTP/HTTPS protocol (supports token authentication)
    """
    SSH = "ssh"
    HTTP = "http"
