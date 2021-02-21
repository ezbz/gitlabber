from gitlabber.naming import FolderNaming
import pytest

def test_naming_parse():
    assert FolderNaming.PATH == FolderNaming.argparse("PATH")

def test_naming_string():
    assert "name" == FolderNaming.__str__(FolderNaming.NAME)


def test_naming_invalid():
    assert "invalid_value" == FolderNaming.argparse("invalid_value")
        
