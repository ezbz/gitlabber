from gitlabber.method import CloneMethod
import pytest
import re

def test_method_parse():
    assert CloneMethod.SSH == CloneMethod.argparse("ssh")

def test_method_string():
    assert "http" == CloneMethod.__str__(CloneMethod.HTTP)

def test_repr():
    retval = repr(CloneMethod.SSH)
    match = re.match("^<CloneMethod: ({.*})>$", retval)


def test_method_invalid():
    assert "invalid_value" == CloneMethod.argparse("invalid_value")
        
