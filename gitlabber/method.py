from typing import Union
import enum


class CloneMethod(enum.IntEnum):
    SSH = 1
    HTTP = 2

    def __str__(self) -> str:
        return self.name.lower()

    def __repr__(self) -> str:
        return str(self)

    @staticmethod
    def argparse(s: str) -> Union['CloneMethod', str]:
        try:
            return CloneMethod[s.upper()]
        except KeyError:
            return s
