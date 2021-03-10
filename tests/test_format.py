from gitlabber.format import PrintFormat
import pytest
import re

def test_format_parse():
    assert PrintFormat.JSON == PrintFormat.argparse("JSON")

def test_format_string():
    assert "json" == PrintFormat.__str__(PrintFormat.JSON)

def test_repr():
    retval = repr(PrintFormat.JSON)
    match = re.match("^<PrintFormat: ({.*})>$", retval)

def test_format_invalid():
    assert "invalid_value" == PrintFormat.argparse("invalid_value")
        
