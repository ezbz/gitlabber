from typing import Union
import enum 

class PrintFormat(enum.IntEnum):
    JSON = 1
    YAML = 2
    TREE = 3

    def __str__(self) -> str:
        return self.name.lower()

    def __repr__(self) -> str:
        return str(self)

    @staticmethod
    def argparse(s: str) -> Union['PrintFormat', str]:
        try:
            return PrintFormat[s.upper()]
        except KeyError:
            return s
