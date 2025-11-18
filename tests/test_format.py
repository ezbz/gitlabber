from gitlabber.format import PrintFormat


def test_format_parse():
    assert PrintFormat.JSON == PrintFormat.argparse("JSON")


def test_format_string():
    assert str(PrintFormat.JSON) == "json"


def test_format_invalid():
    assert PrintFormat.argparse("invalid_value") == "invalid_value"


def test_format_argparse() -> None:
    assert PrintFormat.argparse("json") == PrintFormat.JSON
    assert PrintFormat.argparse("yaml") == PrintFormat.YAML
    assert PrintFormat.argparse("tree") == PrintFormat.TREE
    assert PrintFormat.argparse("invalid") == "invalid"


def test_format_repr() -> None:
    assert repr(PrintFormat.JSON) == "<PrintFormat.JSON: 'json'>"
    assert repr(PrintFormat.YAML) == "<PrintFormat.YAML: 'yaml'>"
    assert repr(PrintFormat.TREE) == "<PrintFormat.TREE: 'tree'>"


def test_format_value_access() -> None:
    assert PrintFormat.JSON.value == "json"
    assert PrintFormat.YAML.value == "yaml"
    assert PrintFormat.TREE.value == "tree"
