from gitlabber.archive import ArchivedResults
import pytest
import re

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
        
