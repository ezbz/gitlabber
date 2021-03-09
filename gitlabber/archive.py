import enum

class ArchivedResults(enum.Enum):
    INCLUDE = (1, None)
    EXCLUDE = (2, False)
    ONLY = (3, True)

    def __init__(self, int_value, api_value):
        self.int_value = int_value
        self.api_value = api_value 

    def __str__(self):
        return self.name.lower()

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        try:
            return ArchivedResults[s.upper()]
        except KeyError:
            return s
