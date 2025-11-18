from gitlabber.naming import FolderNaming


def test_naming_parse():
    assert FolderNaming.PATH == FolderNaming.argparse("PATH")


def test_naming_string():
    assert str(FolderNaming.NAME) == "name"


def test_naming_invalid():
    assert FolderNaming.argparse("invalid_value") == "invalid_value"


def test_naming_argparse() -> None:
    assert FolderNaming.argparse("name") == FolderNaming.NAME
    assert FolderNaming.argparse("path") == FolderNaming.PATH
    assert FolderNaming.argparse("invalid") == "invalid"


def test_naming_repr() -> None:
    assert repr(FolderNaming.NAME) == "FolderNaming.NAME"
    assert repr(FolderNaming.PATH) == "FolderNaming.PATH"


def test_naming_value_access() -> None:
    assert FolderNaming.NAME.value == "name"
    assert FolderNaming.PATH.value == "path"
