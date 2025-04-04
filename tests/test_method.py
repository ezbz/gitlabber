from gitlabber.method import CloneMethod
import pytest
import re
from typing import cast

def test_method_parse():
    assert CloneMethod.SSH == CloneMethod.argparse("ssh")

def test_method_string():
    assert "http" == CloneMethod.__str__(CloneMethod.HTTP)

def test_repr():
    retval = repr(CloneMethod.SSH)
    match = re.match("^<CloneMethod: ({.*})>$", retval)


def test_method_invalid():
    assert "invalid_value" == CloneMethod.argparse("invalid_value")

def test_method_str_representation() -> None:
    assert str(CloneMethod.SSH) == "ssh"
    assert str(CloneMethod.HTTP) == "http"

def test_method_int_values() -> None:
    assert int(CloneMethod.SSH) == 1
    assert int(CloneMethod.HTTP) == 2

def test_method_argparse() -> None:
    assert CloneMethod.argparse("ssh") == CloneMethod.SSH
    assert CloneMethod.argparse("http") == CloneMethod.HTTP
    assert CloneMethod.argparse("invalid") == "invalid"

def test_method_repr() -> None:
    assert repr(CloneMethod.SSH) == "ssh"
    assert repr(CloneMethod.HTTP) == "http"
        
