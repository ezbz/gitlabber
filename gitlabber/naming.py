from typing import Union
import enum 

class FolderNaming(enum.IntEnum):
    NAME = 1
    PATH = 2

    def __str__(self) -> str:
        return self.name.lower()

    def __repr__(self) -> str:
        return str(self)

    @staticmethod
    def argparse(s: str) -> Union['FolderNaming', str]:
        try:
            return FolderNaming[s.upper()]
        except KeyError:
            return s
