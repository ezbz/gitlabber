from typing import Optional
import enum

class ArchivedResults(enum.Enum):
    INCLUDE = (1, None)
    EXCLUDE = (2, False)
    ONLY = (3, True)

    def __init__(self, int_value: int, api_value: Optional[bool]) -> None:
        self.int_value = int_value
        self.api_value = api_value 

    def __str__(self) -> str:
        return self.name.lower()

    def __repr__(self) -> str:
        return str(self)

    @staticmethod
    def argparse(s: str) -> 'ArchivedResults':
        try:
            return ArchivedResults[s.upper()]
        except KeyError:
            return s
