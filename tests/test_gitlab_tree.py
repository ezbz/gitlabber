

import tests.gitlab_test_utils as gitlab_util
import tests.output_test_utils as output_util

def test_load_tree(monkeypatch):
    gl = gitlab_util.create_test_gitlab(monkeypatch)
    gl.load_tree()
    gl.print_tree()
    gitlab_util.validate_tree(gl.root)


def test_filter_tree_include_positive(monkeypatch):
    gl = gitlab_util.create_test_gitlab(monkeypatch, includes=["/group**"])
    gl.load_tree()
    gitlab_util.validate_tree(gl.root)


def test_filter_tree_include_negative(monkeypatch):
    gl = gitlab_util.create_test_gitlab(monkeypatch, includes=["/no_match**"])
    gl.load_tree()
    assert gl.root.is_leaf is True
    assert len(gl.root.children) == 0


def test_filter_tree_exclude_positive(monkeypatch):
    gl = gitlab_util.create_test_gitlab(monkeypatch, excludes=["/group**"])
    gl.load_tree()
    assert gl.root.is_leaf is True
    assert len(gl.root.children) == 0


def test_filter_tree_exclude_deep_positive(monkeypatch):
    gl = gitlab_util.create_test_gitlab(monkeypatch, excludes=["/group/subgroup/project**"])
    gl.load_tree()
    assert gl.root.is_leaf is False
    assert gl.root.height == 2
    assert gl.root.children[0].height == 1


def test_filter_tree_exclude_negative(monkeypatch):
    gl = gitlab_util.create_test_gitlab(monkeypatch, excludes=["/no_match**"])
    gl.load_tree()
    gitlab_util.validate_tree(gl.root)
    
def test_print_tree_json(monkeypatch):
    gl = gitlab_util.create_test_gitlab(monkeypatch)
    gl.load_tree()
    from gitlabber.format import PrintFormat
    import json
    with output_util.captured_output() as (out, err):
        gl.print_tree(PrintFormat.JSON)
        output = json.loads(out.getvalue())
        with open(gitlab_util.JSON_TEST_OUTPUT_FILE, 'r') as jsonFile:
            output_file = json.load(jsonFile)
            assert json.dumps(output_file, sort_keys=True, indent=2) == json.dumps(
                output, sort_keys=True, indent=2)


def test_print_tree_yaml(monkeypatch):
    gl = gitlab_util.create_test_gitlab(monkeypatch)
    gl.load_tree()
    from gitlabber.format import PrintFormat
    import yaml
    with output_util.captured_output() as (out, err):
        gl.print_tree(PrintFormat.YAML)
        output = yaml.safe_load(out.getvalue())
        with open(gitlab_util.YAML_TEST_OUTPUT_FILE, 'r') as yamlFile:
            output_file = yaml.safe_load(yamlFile)
            assert yaml.dump(output_file) == yaml.dump(output)


def test_load_tree_from_file(monkeypatch):
    gl = gitlab_util.create_test_gitlab(
        monkeypatch, in_file=gitlab_util.JSON_TEST_OUTPUT_FILE)
    gl.load_tree()
    gitlab_util.validate_tree(gl.root)


def test_empty_tree(monkeypatch):
    gl = gitlab_util.create_test_gitlab(monkeypatch, excludes=["/group**"])
    gl.load_tree()
    assert gl.is_empty() is True
