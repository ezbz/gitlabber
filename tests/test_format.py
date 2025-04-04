from gitlabber.format import PrintFormat
import pytest
import re
from typing import cast

def test_format_parse():
    assert PrintFormat.JSON == PrintFormat.argparse("JSON")

def test_format_string():
    assert "json" == PrintFormat.__str__(PrintFormat.JSON)

def test_repr():
    retval = repr(PrintFormat.JSON)
    match = re.match("^<PrintFormat: ({.*})>$", retval)

def test_format_invalid():
    assert "invalid_value" == PrintFormat.argparse("invalid_value")

def test_format_str_representation() -> None:
    assert str(PrintFormat.JSON) == "json"
    assert str(PrintFormat.YAML) == "yaml"
    assert str(PrintFormat.TREE) == "tree"

def test_format_int_values() -> None:
    assert int(PrintFormat.JSON) == 1
    assert int(PrintFormat.YAML) == 2
    assert int(PrintFormat.TREE) == 3

def test_format_argparse() -> None:
    assert PrintFormat.argparse("json") == PrintFormat.JSON
    assert PrintFormat.argparse("yaml") == PrintFormat.YAML
    assert PrintFormat.argparse("tree") == PrintFormat.TREE
    assert PrintFormat.argparse("invalid") == "invalid"

def test_format_repr() -> None:
    assert repr(PrintFormat.JSON) == "json"
    assert repr(PrintFormat.YAML) == "yaml"
    assert repr(PrintFormat.TREE) == "tree"
        
