from typing import Union
import enum 

class FolderNaming(enum.StrEnum):
    NAME = "name"
    PATH = "path"

    @staticmethod
    def argparse(s: str) -> Union['FolderNaming', str]:
        try:
            return FolderNaming[s.upper()]
        except KeyError:
            return s
