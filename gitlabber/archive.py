from typing import Optional, Union
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

    @staticmethod
    def argparse(s: str) -> Union['ArchivedResults', str]:
        """Convert a string to an ArchivedResults enum value.
        
        Args:
            s: String to convert
            
        Returns:
            ArchivedResults enum value if successful, original string if not
        """
        try:
            return ArchivedResults[s.upper()]
        except KeyError:
            return s
