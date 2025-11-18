from gitlabber.method import CloneMethod


def test_method_string() -> None:
    assert str(CloneMethod.HTTP) == "http"


def test_method_enum_lookup() -> None:
    assert CloneMethod["SSH"] is CloneMethod.SSH
    assert CloneMethod["HTTP"] is CloneMethod.HTTP


def test_method_repr() -> None:
    assert repr(CloneMethod.SSH) == "<CloneMethod.SSH: 'ssh'>"
    assert repr(CloneMethod.HTTP) == "<CloneMethod.HTTP: 'http'>"


def test_method_value_access() -> None:
    assert CloneMethod.SSH.value == "ssh"
    assert CloneMethod.HTTP.value == "http"
