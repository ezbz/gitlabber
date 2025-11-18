from gitlabber.method import CloneMethod


def test_method_parse():
    assert CloneMethod.argparse("ssh") == CloneMethod.SSH


def test_method_string():
    assert str(CloneMethod.HTTP) == "http"


def test_method_invalid():
    assert CloneMethod.argparse("invalid_value") == "invalid_value"


def test_method_argparse() -> None:
    assert CloneMethod.argparse("ssh") == CloneMethod.SSH
    assert CloneMethod.argparse("http") == CloneMethod.HTTP
    assert CloneMethod.argparse("invalid") == "invalid"


def test_method_repr() -> None:
    assert repr(CloneMethod.SSH) == "CloneMethod.SSH"
    assert repr(CloneMethod.HTTP) == "CloneMethod.HTTP"


def test_method_value_access() -> None:
    assert CloneMethod.SSH.value == "ssh"
    assert CloneMethod.HTTP.value == "http"
