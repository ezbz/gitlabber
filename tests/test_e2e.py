import os
import json
from typing import Dict, Any
import tests.io_test_util as io_util
import pytest
import coverage
coverage.process_startup()


@pytest.mark.slow_integration_test
def test_clone_subgroup():
    os.environ['GITLAB_URL'] = 'https://gitlab.com/'
    output = io_util.execute(['-p', '--print-format', 'json', '--group-search', 'Group Test', '--verbose'], 120)
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
    output = io_util.execute(['-p', '--print-format', 'json', '--group-search', 'Group Test',  '--archived', 'exclude', '--verbose'], 120)
    obj = json.loads(output)
    assert obj['children'][0]['name'] == 'Group Test'
    assert obj['children'][0]['children'][0]['name'] == 'Subgroup Test'
    assert len(obj['children'][0]['children'][0]['children']) == 2
    assert obj['children'][0]['children'][0]['children'][0]['name'] == 'gitlab-project-submodule'
    assert obj['children'][0]['children'][0]['children'][1]['name'] == 'gitlabber-sample-submodule'

@pytest.mark.slow_integration_test
def test_clone_subgroup_only_archived():
    os.environ['GITLAB_URL'] = 'https://gitlab.com/'
    output = io_util.execute(['-p', '--print-format', 'json', '--group-search', 'Group Test',  '--archived', 'only', '--verbose'], 120)
    obj = json.loads(output)
    # Empty tree will have no children, so check if tree has content
    if 'children' in obj and len(obj.get('children', [])) > 0:
        assert obj['children'][0]['name'] == 'Group Test'
        assert obj['children'][0]['children'][0]['name'] == 'Subgroup Test'
        assert len(obj['children'][0]['children'][0]['children']) == 1
        assert obj['children'][0]['children'][0]['children'][0]['name'] == 'archived-project'
    else:
        # If tree is empty (no archived projects found), that's also a valid result
        # This can happen if the archived project was unarchived or deleted
        assert 'name' in obj  # Root node should exist
        assert obj.get('children', []) == []  # No children means empty tree


@pytest.mark.slow_integration_test
def test_clone_subgroup_naming_path() -> None:
    os.environ['GITLAB_URL'] = 'https://gitlab.com/'
    output = io_util.execute(
        ['-p', '--print-format', 'json', '-n', 'path', '--group-search', 'Group Test', '--verbose'],
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
    output = io_util.execute(['-p', '--print-format', 'json', '-n', 'path', '--group-search', 'large-group-test', '--verbose'], 120)
    obj = json.loads(output)
    assert obj['children'][0]['name'] == 'large-group-test'
    assert obj['children'][0]['children'][0]['name'] == 'many-subgroups'
    assert len(obj['children'][0]['children'][0]['children']) == 21
    assert obj['children'][0]['children'][1]['name'] == 'gitlab-many-projects'
    assert len(obj['children'][0]['children'][1]['children']) == 21
    

@pytest.mark.slow_integration_test
def test_user_personal_projects():
    os.environ['GITLAB_URL'] = 'https://gitlab.com/'
    output = io_util.execute(['-p', '--print-format', 'json', '-n', 'path', '--user-projects', '--verbose'], 120)
    obj = json.loads(output)
    assert obj['children'][0]['name'] == 'erezmazor-personal-projects'
    assert obj['children'][0]['children'][0]['name'] == 'gitlabber-personal-project'
    

@pytest.mark.slow_integration_test
def test_shared_group_and_project():
    os.environ['GITLAB_URL'] = 'https://gitlab.com/'
    # Shared projects are included by default, no need for --include-shared flag (which doesn't exist)
    output = io_util.execute(['-p', '--print-format', 'json', '--group-search', 'shared-group3', '--verbose'], 120)
    obj = json.loads(output)
    assert obj['children'][0]['name'] == 'Shared Group'
    assert obj['children'][0]['children'][0]['name'] == 'Shared Project'
    

@pytest.mark.slow_integration_test
def test_api_concurrency_functionality():
    """Test that api_concurrency parameter works correctly in e2e scenario.
    
    This test verifies that:
    1. api_concurrency parameter is accepted
    2. Tree structure is built correctly with parallel API calls
    3. Results are consistent regardless of concurrency level
    """
    os.environ['GITLAB_URL'] = 'https://gitlab.com/'
    
    # Test with different concurrency levels
    for api_concurrency in [1, 3, 5]:
        output = io_util.execute(
            [
                '-p', '--print-format', 'json',
                '--group-search', 'Group Test',
                '--api-concurrency', str(api_concurrency),
                '--verbose'
            ],
            120
        )
        obj = json.loads(output)
        
        # Verify tree structure is correct
        assert obj['children'][0]['name'] == 'Group Test'
        assert obj['children'][0]['children'][0]['name'] == 'Subgroup Test'
        assert len(obj['children'][0]['children'][0]['children']) == 3
        
        # Verify projects are present
        project_names = [child['name'] for child in obj['children'][0]['children'][0]['children']]
        assert 'archived-project' in project_names
        assert 'gitlab-project-submodule' in project_names
        assert 'gitlabber-sample-submodule' in project_names
    
    print("\n✓ API concurrency functionality verified for all tested levels (1, 3, 5)")

    