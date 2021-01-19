from gitlabber.method import CloneMethod
import pytest

def test_method_parse():
    assert CloneMethod.SSH == CloneMethod.argparse("ssh")

def test_method_string():
    assert "https" == CloneMethod.__str__(CloneMethod.HTTPS)


def test_method_invalid():
    assert "invalid_value" == CloneMethod.argparse("invalid_value")
        
