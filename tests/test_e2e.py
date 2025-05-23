import os
import json
from gitlabber import __version__ as VERSION
import tests.gitlab_test_utils as gitlab_util
import tests.io_test_util as io_util
import pytest
import coverage
from typing import Dict, Any, cast
coverage.process_startup()


@pytest.mark.slow_integration_test
def test_clone_subgroup():
    os.environ['GITLAB_URL'] = 'https://gitlab.com/'
    output = io_util.execute(['-p', '--print-format', 'json', '--group-search', 'Group Test'], 120)
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
    output = io_util.execute(['-p', '--print-format', 'json', '--group-search', 'Group Test',  '-a', 'exclude'], 120)
    obj = json.loads(output)
    assert obj['children'][0]['name'] == 'Group Test'
    assert obj['children'][0]['children'][0]['name'] == 'Subgroup Test'
    assert len(obj['children'][0]['children'][0]['children']) == 2
    assert obj['children'][0]['children'][0]['children'][0]['name'] == 'gitlab-project-submodule'
    assert obj['children'][0]['children'][0]['children'][1]['name'] == 'gitlabber-sample-submodule'

@pytest.mark.slow_integration_test
def test_clone_subgroup_only_archived():
    os.environ['GITLAB_URL'] = 'https://gitlab.com/'
    output = io_util.execute(['-p', '--print-format', 'json', '--group-search', 'Group Test',  '-a', 'only'], 120)
    obj = json.loads(output)
    assert obj['children'][0]['name'] == 'Group Test'
    assert obj['children'][0]['children'][0]['name'] == 'Subgroup Test'
    assert len(obj['children'][0]['children'][0]['children']) == 1
    assert obj['children'][0]['children'][0]['children'][0]['name'] == 'archived-project'


@pytest.mark.slow_integration_test
def test_clone_subgroup_naming_path() -> None:
    os.environ['GITLAB_URL'] = 'https://gitlab.com/'
    output = io_util.execute(
        ['-p', '--print-format', 'json', '-n', 'path', '--group-search', 'Group Test'],
        120
    )
    obj: Dict[str, Any] = json.loads(output)
    
    assert obj['children'][0]['name'] == 'erez-group-test'
    assert obj['children'][0]['children'][0]['name'] == 'subgroup-test'
    assert len(obj['children'][0]['children'][0]['children']) == 3
    assert obj['children'][0]['children'][0]['children'][0]['name'] == 'archived-project'
    assert obj['children'][0]['children'][0]['children'][1]['name'] == 'gitlab-project-submodule'
    assert obj['children'][0]['children'][0]['children'][2]['name'] == 'gitlabber-sample-submodule'


@pytest.mark.slow_integration_test
def test_large_groups():
    os.environ['GITLAB_URL'] = 'https://gitlab.com/'
    output = io_util.execute(['-p', '--print-format', 'json', '-n', 'path', '--group-search', 'large-group-test'], 120)
    obj = json.loads(output)
    assert obj['children'][0]['name'] == 'large-group-test'
    assert obj['children'][0]['children'][0]['name'] == 'many-subgroups'
    assert len(obj['children'][0]['children'][0]['children']) == 21
    assert obj['children'][0]['children'][1]['name'] == 'gitlab-many-projects'
    assert len(obj['children'][0]['children'][1]['children']) == 21
    

@pytest.mark.slow_integration_test
def test_user_personal_projects():
    os.environ['GITLAB_URL'] = 'https://gitlab.com/'
    output = io_util.execute(['-p', '--print-format', 'json', '-n', 'path', '--user-projects'], 120)
    obj = json.loads(output)
    assert obj['children'][0]['name'] == 'erezmazor-personal-projects'
    assert obj['children'][0]['children'][0]['name'] == 'gitlabber-personal-project'
    

@pytest.mark.slow_integration_test
def test_shared_group_and_project():
    os.environ['GITLAB_URL'] = 'https://gitlab.com/'
    output = io_util.execute(['-p', '--print-format', 'json', '-s', '--group-search', 'shared-group3'], 120)
    obj = json.loads(output)
    assert obj['children'][0]['name'] == 'Shared Group'
    assert obj['children'][0]['children'][0]['name'] == 'Shared Project'
    
    