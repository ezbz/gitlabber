from gitlabber.naming import FolderNaming


def test_naming_string() -> None:
    assert str(FolderNaming.NAME) == "name"


def test_naming_enum_lookup() -> None:
    assert FolderNaming["NAME"] is FolderNaming.NAME
    assert FolderNaming["PATH"] is FolderNaming.PATH


def test_naming_repr() -> None:
    assert repr(FolderNaming.NAME) == "<FolderNaming.NAME: 'name'>"
    assert repr(FolderNaming.PATH) == "<FolderNaming.PATH: 'path'>"


def test_naming_value_access() -> None:
    assert FolderNaming.NAME.value == "name"
    assert FolderNaming.PATH.value == "path"
