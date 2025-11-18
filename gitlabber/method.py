from typing import Union
import enum


class CloneMethod(enum.StrEnum):
    SSH = "ssh"
    HTTP = "http"

    @staticmethod
    def argparse(s: str) -> Union['CloneMethod', str]:
        try:
            return CloneMethod[s.upper()]
        except KeyError:
            return s
