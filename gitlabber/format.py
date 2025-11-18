from typing import Union
import enum 

class PrintFormat(enum.StrEnum):
    JSON = "json"
    YAML = "yaml"
    TREE = "tree"

    @staticmethod
    def argparse(s: str) -> Union['PrintFormat', str]:
        try:
            return PrintFormat[s.upper()]
        except KeyError:
            return s
