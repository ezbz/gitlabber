"""Enumeration for handling archived GitLab projects and groups.

This module provides the ArchivedResults enum which controls how archived
projects and groups are handled during tree building and filtering.
"""

from typing import Optional
import enum


class ArchivedResults(enum.Enum):
    """Enumeration for handling archived results in GitLab projects.
    
    Attributes:
        INCLUDE: Include both archived and non-archived projects
        EXCLUDE: Exclude archived projects
        ONLY: Only include archived projects
    """
    INCLUDE = (1, None)
    EXCLUDE = (2, False)
    ONLY = (3, True)

    def __init__(self, int_value: int, api_value: Optional[bool]) -> None:
        """Initialize the enum value.
        
        Args:
            int_value: Integer value for internal use
            api_value: Boolean value for GitLab API, None for INCLUDE
        """
        self.int_value = int_value
        self.api_value = api_value 

    def __str__(self) -> str:
        """Return the lowercase name of the enum value."""
        return self.name.lower()

    def __repr__(self) -> str:
        """Return the string representation of the enum value."""
        return str(self)

