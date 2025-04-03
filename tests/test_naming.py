from gitlabber.naming import FolderNaming
import pytest
import re
from typing import cast

def test_naming_parse():
    assert FolderNaming.PATH == FolderNaming.argparse("PATH")

def test_naming_string():
    assert "name" == FolderNaming.__str__(FolderNaming.NAME)

def test_repr():
    retval = repr(FolderNaming.PATH)
    match = re.match("^<FolderNaming: ({.*})>$", retval)

def test_naming_invalid():
    assert "invalid_value" == FolderNaming.argparse("invalid_value")

def test_naming_str_representation() -> None:
    assert str(FolderNaming.NAME) == "name"
    assert str(FolderNaming.PATH) == "path"

def test_naming_int_values() -> None:
    assert int(FolderNaming.NAME) == 1
    assert int(FolderNaming.PATH) == 2

def test_naming_argparse() -> None:
    assert FolderNaming.argparse("name") == FolderNaming.NAME
    assert FolderNaming.argparse("path") == FolderNaming.PATH
    assert FolderNaming.argparse("invalid") == "invalid"

def test_naming_repr() -> None:
    assert repr(FolderNaming.NAME) == "name"
    assert repr(FolderNaming.PATH) == "path"
        
