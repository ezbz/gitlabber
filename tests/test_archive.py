from gitlabber.archive import ArchivedResults
import pytest
import re
from typing import cast

def test_archive_parse():
    assert ArchivedResults.INCLUDE == ArchivedResults.argparse("include")

def test_archive_string():
    assert "exclude" == ArchivedResults.__str__(ArchivedResults.EXCLUDE)

def test_repr():
    retval = repr(ArchivedResults.ONLY)
    match = re.match("^<ArchivedResults: ({.*})>$", retval)

def test_archive_api_value():
    assert True == ArchivedResults.ONLY.api_value
    assert False == ArchivedResults.EXCLUDE.api_value
    assert None == ArchivedResults.INCLUDE.api_value

def test_archive_invalid():
    assert "invalid_value" == ArchivedResults.argparse("invalid_value")

def test_archive_str_representation() -> None:
    assert str(ArchivedResults.INCLUDE) == "include"
    assert str(ArchivedResults.EXCLUDE) == "exclude"
    assert str(ArchivedResults.ONLY) == "only"

def test_archive_api_values() -> None:
    assert ArchivedResults.INCLUDE.api_value is None
    assert ArchivedResults.EXCLUDE.api_value is False
    assert ArchivedResults.ONLY.api_value is True

def test_archive_int_values() -> None:
    assert ArchivedResults.INCLUDE.int_value == 1
    assert ArchivedResults.EXCLUDE.int_value == 2
    assert ArchivedResults.ONLY.int_value == 3

def test_archive_argparse() -> None:
    assert ArchivedResults.argparse("include") == ArchivedResults.INCLUDE
    assert ArchivedResults.argparse("exclude") == ArchivedResults.EXCLUDE
    assert ArchivedResults.argparse("only") == ArchivedResults.ONLY
    assert ArchivedResults.argparse("invalid") == "invalid"
        
