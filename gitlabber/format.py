"""Output format enumeration for tree printing.

This module defines the available output formats for displaying
the GitLab project tree structure.
"""

import enum


class PrintFormat(enum.StrEnum):
    """Output format for tree printing operations.
    
    Attributes:
        JSON: Output as JSON format
        YAML: Output as YAML format
        TREE: Output as a hierarchical tree structure
    """
    JSON = "json"
    YAML = "yaml"
    TREE = "tree"
