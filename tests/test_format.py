from gitlabber.format import PrintFormat


def test_format_string() -> None:
    assert str(PrintFormat.JSON) == "json"


def test_format_enum_lookup() -> None:
    assert PrintFormat["JSON"] is PrintFormat.JSON
    assert PrintFormat["YAML"] is PrintFormat.YAML
    assert PrintFormat["TREE"] is PrintFormat.TREE


def test_format_repr() -> None:
    assert repr(PrintFormat.JSON) == "<PrintFormat.JSON: 'json'>"
    assert repr(PrintFormat.YAML) == "<PrintFormat.YAML: 'yaml'>"
    assert repr(PrintFormat.TREE) == "<PrintFormat.TREE: 'tree'>"


def test_format_value_access() -> None:
    assert PrintFormat.JSON.value == "json"
    assert PrintFormat.YAML.value == "yaml"
    assert PrintFormat.TREE.value == "tree"
