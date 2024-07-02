import os
import json
from gitlabber import __version__ as VERSION
import tests.gitlab_test_utils as gitlab_util
import tests.io_test_util as io_util
import pytest
import coverage
coverage.process_startup()


@pytest.mark.slow_integration_test
def test_clone_subgroup():
    os.environ['GITLAB_URL'] = 'https://gitlab.com/'
    output = io_util.execute(['-p', '--print-format', 'json', '--group-search', 'Group Test'], 60)
    obj = json.loads(output)
    assert obj['children'][0]['name'] == 'Group Test'
    assert obj['children'][0]['children'][0]['name'] == 'Subgroup Test'
    assert len(obj['children'][0]['children'][0]['children']) == 3
    assert obj['children'][0]['children'][0]['children'][0]['name'] == 'archived-project'
    assert obj['children'][0]['children'][0]['children'][1]['name'] == 'gitlab-project-submodule'
    assert obj['children'][0]['children'][0]['children'][2]['name'] == 'gitlabber-sample-submodule'

@pytest.mark.slow_integration_test
def test_clone_subgroup_exclude_archived():
    os.environ['GITLAB_URL'] = 'https://gitlab.com/'
    output = io_util.execute(['-p', '--print-format', 'json', '--group-search', 'Group Test',  '-a', 'exclude'], 60)
    obj = json.loads(output)
    assert obj['children'][0]['name'] == 'Group Test'
    assert obj['children'][0]['children'][0]['name'] == 'Subgroup Test'
    assert len(obj['children'][0]['children'][0]['children']) == 2
    assert obj['children'][0]['children'][0]['children'][0]['name'] == 'gitlab-project-submodule'
    assert obj['children'][0]['children'][0]['children'][1]['name'] == 'gitlabber-sample-submodule'

@pytest.mark.slow_integration_test
def test_clone_subgroup_only_archived():
    os.environ['GITLAB_URL'] = 'https://gitlab.com/'
    output = io_util.execute(['-p', '--print-format', 'json', '--group-search', 'Group Test',  '-a', 'only'], 60)
    obj = json.loads(output)
    assert obj['children'][0]['name'] == 'Group Test'
    assert obj['children'][0]['children'][0]['name'] == 'Subgroup Test'
    assert len(obj['children'][0]['children'][0]['children']) == 1
    assert obj['children'][0]['children'][0]['children'][0]['name'] == 'archived-project'


@pytest.mark.slow_integration_test
def test_clone_subgroup_naming_path():
    os.environ['GITLAB_URL'] = 'https://gitlab.com/'
    output = io_util.execute(['-p', '--print-format', 'json', '-n', 'path', '--group-search', 'Group Test'], 60)
    obj = json.loads(output)
    assert obj['children'][0]['name'] == 'erez-group-test'
    assert obj['children'][0]['children'][0]['name'] == 'subgroup-test'
    assert len(obj['children'][0]['children'][0]['children']) == 3
    assert obj['children'][0]['children'][0]['children'][0]['name'] == 'archived-project'
    assert obj['children'][0]['children'][0]['children'][1]['name'] == 'gitlab-project-submodule'
    assert obj['children'][0]['children'][0]['children'][2]['name'] == 'gitlabber-sample-submodule'


@pytest.mark.slow_integration_test
def test_large_groups():
    os.environ['GITLAB_URL'] = 'https://gitlab.com/'
    output = io_util.execute(['-p', '--print-format', 'json', '-n', 'path', '--group-search', 'large-group-test'], 60)
    obj = json.loads(output)
    assert obj['children'][0]['name'] == 'large-group-test'
    assert obj['children'][0]['children'][0]['name'] == 'many-subgroups'
    assert len(obj['children'][0]['children'][0]['children']) == 21
    assert obj['children'][0]['children'][1]['name'] == 'gitlab-many-projects'
    assert len(obj['children'][0]['children'][1]['children']) == 21
    

@pytest.mark.slow_integration_test
def test_user_personal_projects():
    os.environ['GITLAB_URL'] = 'https://gitlab.com/'
    output = io_util.execute(['-p', '--print-format', 'json', '-n', 'path', '--user-projects'], 60)
    obj = json.loads(output)
    assert obj['children'][0]['name'] == 'erezmazor-prsonal-projects'
    assert obj['children'][0]['children'][0]['name'] == 'gitlabber-personal-project'
    