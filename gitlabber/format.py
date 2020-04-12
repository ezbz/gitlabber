import enum 

class PrintFormat(enum.IntEnum):
    JSON = 1
    YAML = 2
    TREE = 3

    def __str__(self):
        return self.name.lower()

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        try:
            return PrintFormat[s.upper()]
        except KeyError:
            return s
