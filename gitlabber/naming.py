"""Folder naming strategy enumeration.

This module defines how project folders should be named when cloning
the GitLab project hierarchy.
"""

import enum


class FolderNaming(enum.StrEnum):
    """Strategy for naming project folders.
    
    Attributes:
        NAME: Use the project name only (e.g., "my-project")
        PATH: Use the full project path (e.g., "group/subgroup/my-project")
    """
    NAME = "name"
    PATH = "path"
