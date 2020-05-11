import enum


class CloneMethod(enum.IntEnum):
    SSH = 1
    HTTP = 2

    def __str__(self):
        return self.name.lower()

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        try:
            return CloneMethod[s.upper()]
        except KeyError:
            return s
