import enum 

class FolderNaming(enum.IntEnum):
    NAME = 1
    PATH = 2

    def __str__(self):
        return self.name.lower()

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        try:
            return FolderNaming[s.upper()]
        except KeyError:
            return s
