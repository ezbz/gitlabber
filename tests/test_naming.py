from gitlabber.naming import FolderNaming
import pytest
import re

def test_naming_parse():
    assert FolderNaming.PATH == FolderNaming.argparse("PATH")

def test_naming_string():
    assert "name" == FolderNaming.__str__(FolderNaming.NAME)

def test_repr():
    retval = repr(FolderNaming.PATH)
    match = re.match("^<FolderNaming: ({.*})>$", retval)

def test_naming_invalid():
    assert "invalid_value" == FolderNaming.argparse("invalid_value")
        
