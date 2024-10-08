# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import re
from typing import Union

import pytest

from config import ConfigClass


@pytest.fixture
def mock_metadata_item():
    def _mock_metadata_item(zone: Union[int, str]):
        return {
            'zone': zone,
        }

    yield _mock_metadata_item


async def test_search_replaces_zone_numbers_in_response_with_string_values(
    mocker, test_async_client, httpx_mock, project_factory, mock_metadata_item, has_permission_true
):
    mocker.patch('app.auth.get_current_identity', return_value={'role': 'admin', 'username': 'admin'})
    project = project_factory.mock_retrieval_by_code()
    httpx_mock.add_response(
        method='GET',
        url=re.compile(rf'^{ConfigClass.SEARCH_SERVICE}/v1/metadata-items/.*?container_code={project.code}.*$'),
        json={
            'result': [mock_metadata_item(0), mock_metadata_item(1), mock_metadata_item(2)],
        },
    )
    expected_response = {
        'result': [
            mock_metadata_item(ConfigClass.GREENROOM_ZONE_LABEL),
            mock_metadata_item(ConfigClass.CORE_ZONE_LABEL),
            mock_metadata_item('2'),
        ],
    }

    headers = {'Authorization': ''}
    response = await test_async_client.get(f'/v1/project-files/{project.code}/search', headers=headers)

    assert response.status_code == 200

    assert response.json() == expected_response


async def test_search_replaces_zone_numbers_in_query_params_with_string_values(
    mocker, test_async_client, httpx_mock, project_factory, has_permission_true
):
    mocker.patch('app.auth.get_current_identity', return_value={'role': 'admin', 'username': 'admin'})
    project = project_factory.mock_retrieval_by_code()
    httpx_mock.add_response(
        method='GET',
        url=re.compile(rf'^{ConfigClass.SEARCH_SERVICE}/v1/metadata-items/.*?zone=1.*$'),
        json={'result': []},
    )

    headers = {'Authorization': ''}
    params = {'zone': ConfigClass.CORE_ZONE_LABEL}
    response = await test_async_client.get(
        f'/v1/project-files/{project.code}/search', headers=headers, query_string=params
    )

    assert response.status_code == 200


@pytest.mark.parametrize(
    'role,params,expected_search_params',
    [
        ('admin', {}, {'zone': 0}),
        ('admin', {'zone': ConfigClass.GREENROOM_ZONE_LABEL}, {'zone': 0}),
        ('admin', {'zone': ConfigClass.CORE_ZONE_LABEL}, {'zone': 1}),
    ],
)
async def test_search_overrides_search_service_query_params_admin(
    role,
    params,
    expected_search_params,
    mocker,
    test_async_client,
    httpx_mock,
    project_factory,
    has_admin_file_permission,
):
    project = project_factory.mock_retrieval_by_code()
    mocker.patch(
        'app.auth.get_current_identity',
        return_value={'role': 'member', 'username': role, 'realm_roles': [f'{project.code}-{role}']},
    )
    expected_query = '&'.join(f'{k}={v}' for k, v in expected_search_params.items())
    expected_query = f'{expected_query}&container_type=project&container_code={project.code}'
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.SEARCH_SERVICE}/v1/metadata-items/?{expected_query}',
        json={'result': []},
    )

    headers = {'Authorization': ''}
    response = await test_async_client.get(
        f'/v1/project-files/{project.code}/search', headers=headers, query_string=params
    )

    httpx_mock.reset(False)
    assert response.status_code == 200


@pytest.mark.parametrize(
    'role,params,expected_search_params',
    [
        (
            'collaborator',
            {},
            {'zone': 0, 'parent_path': 'collaborator%'},
        ),
        (
            'collaborator',
            {'zone': ConfigClass.GREENROOM_ZONE_LABEL},
            {'zone': 0, 'parent_path': 'collaborator%'},
        ),
        (
            'collaborator',
            {'zone': ConfigClass.GREENROOM_ZONE_LABEL, 'parent_path': 'custom'},
            {'zone': 0, 'parent_path': 'collaborator%'},
        ),
        (
            'collaborator',
            {'zone': ConfigClass.CORE_ZONE_LABEL},
            {'zone': 1},
        ),
        (
            'collaborator',
            {'zone': ConfigClass.CORE_ZONE_LABEL, 'parent_path': 'custom'},
            {'zone': 1, 'parent_path': 'custom'},
        ),
    ],
)
async def test_search_overrides_search_service_query_params_collab(
    role,
    params,
    expected_search_params,
    mocker,
    test_async_client,
    httpx_mock,
    project_factory,
    has_collab_file_permission,
):
    project = project_factory.mock_retrieval_by_code()
    mocker.patch(
        'app.auth.get_current_identity',
        return_value={'role': role, 'username': role, 'realm_roles': [f'{project.code}-{role}']},
    )
    expected_query = '&'.join(f'{k}={v}' for k, v in expected_search_params.items())
    expected_query = f'{expected_query}&container_type=project&container_code={project.code}'
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.SEARCH_SERVICE}/v1/metadata-items/?{expected_query}',
        json={'result': []},
    )

    headers = {'Authorization': ''}
    response = await test_async_client.get(
        f'/v1/project-files/{project.code}/search', headers=headers, query_string=params
    )

    httpx_mock.reset(False)
    assert response.status_code == 200


@pytest.mark.parametrize(
    'role,params,expected_search_params',
    [
        (
            'contributor',
            {},
            {'zone': 0, 'parent_path': 'contributor%'},
        ),
        (
            'contributor',
            {'zone': ConfigClass.GREENROOM_ZONE_LABEL},
            {'zone': 0, 'parent_path': 'contributor%'},
        ),
        (
            'contributor',
            {'zone': ConfigClass.GREENROOM_ZONE_LABEL, 'parent_path': 'custom'},
            {'zone': 0, 'parent_path': 'contributor%'},
        ),
    ],
)
async def test_search_overrides_search_service_query_params_contrib(
    role,
    params,
    expected_search_params,
    mocker,
    test_async_client,
    httpx_mock,
    project_factory,
    has_contrib_file_permission,
):
    project = project_factory.mock_retrieval_by_code()
    mocker.patch(
        'app.auth.get_current_identity',
        return_value={'role': role, 'username': role, 'realm_roles': [f'{project.code}-{role}']},
    )
    expected_query = '&'.join(f'{k}={v}' for k, v in expected_search_params.items())
    expected_query = f'{expected_query}&container_type=project&container_code={project.code}'
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.SEARCH_SERVICE}/v1/metadata-items/?{expected_query}',
        json={'result': []},
    )

    headers = {'Authorization': ''}
    response = await test_async_client.get(
        f'/v1/project-files/{project.code}/search', headers=headers, query_string=params
    )

    httpx_mock.reset(False)
    assert response.status_code == 200


@pytest.mark.parametrize(
    'role, expected_response, search_response',
    [
        (
            'admin',
            {
                'data': {
                    'labels': ['2022-01', '2022-02', '2022-03'],
                    'datasets': [
                        {'label': ConfigClass.GREENROOM_ZONE_LABEL, 'values': [536870912, 715827882, 920350134]},
                        {'label': ConfigClass.CORE_ZONE_LABEL, 'values': [107374182, 143165576, 184070026]},
                    ],
                }
            },
            {
                'data': {
                    'labels': ['2022-01', '2022-02', '2022-03'],
                    'datasets': [
                        {'label': 0, 'values': [536870912, 715827882, 920350134]},
                        {'label': 1, 'values': [107374182, 143165576, 184070026]},
                    ],
                }
            },
        ),
    ],
)
async def test_size_endpoint_returns_search_service_response_admin(
    role,
    search_response,
    expected_response,
    mocker,
    test_async_client,
    httpx_mock,
    project_factory,
    jwt_token_project_admin,
    has_permission_true,
):
    project = project_factory.generate(code='test_project')
    project_factory.mock_retrieval_by_code(project)
    user = 'testuser'
    mocker.patch(
        'app.auth.get_current_identity',
        return_value={'role': 'member', 'username': user, 'realm_roles': [f'{project.code}-{role}']},
    )

    url = f'{ConfigClass.SEARCH_SERVICE}/v1/project-files/{project.code}/size'

    if role == 'collaborator' or role == 'contributor':
        httpx_mock.add_response(method='GET', url=f'{url}?parent_path={user}%', json=search_response)

    if role != 'contributor':
        httpx_mock.add_response(
            method='GET',
            url=url,
            json=search_response,
        )
    headers = {'Authorization': ''}
    response = await test_async_client.get(f'/v1/project-files/{project.code}/size', headers=headers)
    assert response.status_code == 200

    assert response.json() == expected_response


@pytest.mark.parametrize(
    'role, expected_response, search_response',
    [
        (
            'collaborator',
            {
                'data': {
                    'labels': ['2022-01', '2022-02', '2022-03'],
                    'datasets': [
                        {'label': ConfigClass.GREENROOM_ZONE_LABEL, 'values': [444870912, 555827882, 0]},
                        {'label': ConfigClass.CORE_ZONE_LABEL, 'values': [27456, 39012, 0]},
                    ],
                }
            },
            {
                'data': {
                    'labels': ['2022-01', '2022-02', '2022-03'],
                    'datasets': [
                        {'label': 0, 'values': [444870912, 555827882, 0]},
                        {'label': 1, 'values': [27456, 39012, 0]},
                    ],
                }
            },
        ),
    ],
)
async def test_size_endpoint_returns_search_service_response_collab(
    role,
    search_response,
    expected_response,
    mocker,
    test_async_client,
    httpx_mock,
    project_factory,
    jwt_token_collab,
    has_collab_file_permission,
):
    project = project_factory.generate(code='test_project')
    project_factory.mock_retrieval_by_code(project)
    user = 'testuser'
    mocker.patch(
        'app.auth.get_current_identity',
        return_value={'role': role, 'username': user, 'realm_roles': [f'{project.code}-{role}']},
    )

    url = (
        f'{ConfigClass.AUTH_SERVICE}authorize?role=collaborator&resource=project&zone=%2A&operation=view'
        f'&project_code=test_project'
    )
    httpx_mock.add_response(
        method='GET',
        url=url,
        json={'result': {'has_permission': True}},
    )

    url = f'{ConfigClass.SEARCH_SERVICE}/v1/project-files/{project.code}/size'

    if role == 'collaborator' or role == 'contributor':
        httpx_mock.add_response(method='GET', url=f'{url}?parent_path={user}%', json=search_response)

    if role != 'contributor':
        httpx_mock.add_response(
            method='GET',
            url=url,
            json=search_response,
        )
    headers = {'Authorization': ''}
    response = await test_async_client.get(f'/v1/project-files/{project.code}/size', headers=headers)
    assert response.status_code == 200

    assert response.json() == expected_response


@pytest.mark.parametrize(
    'role, expected_response, search_response',
    [
        (
            'contributor',
            {
                'data': {
                    'labels': ['2022-01', '2022-02', '2022-03'],
                    'datasets': [
                        {'label': ConfigClass.GREENROOM_ZONE_LABEL, 'values': [1, 0, 0]},
                    ],
                }
            },
            {
                'data': {
                    'labels': ['2022-01', '2022-02', '2022-03'],
                    'datasets': [
                        {'label': 0, 'values': [1, 0, 0]},
                    ],
                }
            },
        ),
    ],
)
async def test_size_endpoint_returns_search_service_response_contrib(
    role,
    search_response,
    expected_response,
    mocker,
    test_async_client,
    httpx_mock,
    project_factory,
    jwt_token_contrib,
    has_contrib_file_permission,
):
    project = project_factory.generate(code='test_project')
    project_factory.mock_retrieval_by_code(project)
    user = 'testuser'
    mocker.patch(
        'app.auth.get_current_identity',
        return_value={'role': role, 'username': user, 'realm_roles': [f'{project.code}-{role}']},
    )

    url = (
        f'{ConfigClass.AUTH_SERVICE}authorize?role=contributor&resource=project&zone=%2A&operation=view'
        f'&project_code=test_project'
    )
    httpx_mock.add_response(
        method='GET',
        url=url,
        json={'result': {'has_permission': True}},
    )

    url = f'{ConfigClass.SEARCH_SERVICE}/v1/project-files/{project.code}/size'

    if role == 'collaborator' or role == 'contributor':
        httpx_mock.add_response(method='GET', url=f'{url}?parent_path={user}%', json=search_response)

    if role != 'contributor':
        httpx_mock.add_response(
            method='GET',
            url=url,
            json=search_response,
        )
    headers = {'Authorization': ''}
    response = await test_async_client.get(f'/v1/project-files/{project.code}/size', headers=headers)
    assert response.status_code == 200

    assert response.json() == expected_response


@pytest.mark.parametrize(
    'role,expected_datasets',
    [
        ('admin', [{'label': 'Greenroom', 'values': [0, 0, 0]}, {'label': 'Core', 'values': [0, 0, 0]}]),
    ],
)
async def test_size_endpoint_substitutes_dataset_entries_when_they_are_empty_admin(
    role,
    expected_datasets,
    mocker,
    test_async_client,
    httpx_mock,
    project_factory,
    jwt_token_project_admin,
    has_admin_file_permission,
):
    project = project_factory.generate(code='test_project')
    project_factory.mock_retrieval_by_code(project)
    user = 'testuser'
    mocker.patch(
        'app.auth.get_current_identity',
        return_value={'role': 'member', 'username': user, 'realm_roles': [f'{project.code}-{role}']},
    )

    url = (
        f'{ConfigClass.AUTH_SERVICE}authorize?role=admin&resource=project&zone=%2A&operation=view'
        f'&project_code=test_project'
    )
    httpx_mock.add_response(
        method='GET',
        url=url,
        json={'result': {'has_permission': True}},
    )

    httpx_mock.add_response(
        method='GET',
        url=re.compile(rf'^{ConfigClass.SEARCH_SERVICE}/v1/project-files/{project.code}/size'),
        json={'data': {'datasets': [], 'labels': ['2022-01', '2022-02', '2022-02']}},
    )

    headers = {'Authorization': ''}
    response = await test_async_client.get(f'/v1/project-files/{project.code}/size', headers=headers)
    assert response.status_code == 200

    assert response.json()['data']['datasets'] == expected_datasets


@pytest.mark.parametrize(
    'role,expected_datasets',
    [
        ('collaborator', [{'label': 'Greenroom', 'values': [0, 0, 0]}, {'label': 'Core', 'values': [0, 0, 0]}]),
    ],
)
async def test_size_endpoint_substitutes_dataset_entries_when_they_are_empty_collab(
    role,
    expected_datasets,
    mocker,
    test_async_client,
    httpx_mock,
    project_factory,
    jwt_token_collab,
    has_collab_file_permission,
):
    project = project_factory.generate(code='test_project')
    project_factory.mock_retrieval_by_code(project)
    user = 'testuser'
    mocker.patch(
        'app.auth.get_current_identity',
        return_value={'role': 'member', 'username': user, 'realm_roles': [f'{project.code}-{role}']},
    )

    url = (
        f'{ConfigClass.AUTH_SERVICE}authorize?role=collaborator&resource=project&zone=%2A&operation=view'
        f'&project_code=test_project'
    )
    httpx_mock.add_response(
        method='GET',
        url=url,
        json={'result': {'has_permission': True}},
    )

    httpx_mock.add_response(
        method='GET',
        url=re.compile(rf'^{ConfigClass.SEARCH_SERVICE}/v1/project-files/{project.code}/size'),
        json={'data': {'datasets': [], 'labels': ['2022-01', '2022-02', '2022-02']}},
    )

    headers = {'Authorization': ''}
    response = await test_async_client.get(f'/v1/project-files/{project.code}/size', headers=headers)
    assert response.status_code == 200

    assert response.json()['data']['datasets'] == expected_datasets


@pytest.mark.parametrize(
    'role,expected_datasets',
    [
        ('contributor', [{'label': 'Greenroom', 'values': [0, 0, 0]}]),
    ],
)
async def test_size_endpoint_substitutes_dataset_entries_when_they_are_empty(
    role,
    expected_datasets,
    mocker,
    test_async_client,
    httpx_mock,
    project_factory,
    jwt_token_contrib,
    has_contrib_file_permission,
):
    project = project_factory.generate(code='test_project')
    project_factory.mock_retrieval_by_code(project)
    user = 'testuser'
    mocker.patch(
        'app.auth.get_current_identity',
        return_value={'role': role, 'username': user, 'realm_roles': [f'{project.code}-{role}']},
    )

    url = (
        f'{ConfigClass.AUTH_SERVICE}authorize?role=contributor&resource=project&zone=%2A&operation=view'
        f'&project_code=test_project'
    )
    httpx_mock.add_response(
        method='GET',
        url=url,
        json={'result': {'has_permission': True}},
    )

    httpx_mock.add_response(
        method='GET',
        url=re.compile(rf'^{ConfigClass.SEARCH_SERVICE}/v1/project-files/{project.code}/size'),
        json={'data': {'datasets': [], 'labels': ['2022-01', '2022-02', '2022-02']}},
    )

    headers = {'Authorization': ''}
    response = await test_async_client.get(f'/v1/project-files/{project.code}/size', headers=headers)
    assert response.status_code == 200

    assert response.json()['data']['datasets'] == expected_datasets


@pytest.mark.parametrize(
    'role, search_response, expected_response',
    [
        (
            'admin',
            {
                ConfigClass.GREENROOM_ZONE_LABEL: {
                    'files': {
                        'total_count': 5,
                        'total_size': 500,
                    },
                    'activity': {'today_uploaded': 1, 'today_downloaded': 1},
                },
                ConfigClass.CORE_ZONE_LABEL: {
                    'files': {
                        'total_count': 5,
                        'total_size': 500,
                    },
                    'activity': {'today_uploaded': 1, 'today_downloaded': 1},
                },
            },
            {
                'files': {
                    'total_count': 10,
                    'total_size': 1000,
                    'total_per_zone': {
                        ConfigClass.GREENROOM_ZONE_LABEL.lower(): 5,
                        ConfigClass.CORE_ZONE_LABEL.lower(): 5,
                    },
                },
                'activity': {'today_uploaded': 2, 'today_downloaded': 2},
            },
        ),
    ],
)
async def test_statistics_endpoint_returns_search_service_response_limited_admin(
    role,
    search_response,
    expected_response,
    mocker,
    test_async_client,
    httpx_mock,
    project_factory,
    has_admin_file_permission,
):
    project = project_factory.mock_retrieval_by_code()

    mocker.patch(
        'app.auth.get_current_identity',
        return_value={'role': 'member', 'username': role, 'realm_roles': [f'{project.code}-{role}']},
    )

    httpx_mock.add_response(
        method='GET',
        url=re.compile(rf'^{ConfigClass.SEARCH_SERVICE}/v1/project-files/{project.code}/statistics\?zone=0'),
        json=search_response[ConfigClass.GREENROOM_ZONE_LABEL],
    )
    httpx_mock.add_response(
        method='GET',
        url=re.compile(rf'^{ConfigClass.SEARCH_SERVICE}/v1/project-files/{project.code}/statistics\?zone=1'),
        json=search_response[ConfigClass.GREENROOM_ZONE_LABEL],
    )

    headers = {'Authorization': ''}
    response = await test_async_client.get(f'/v1/project-files/{project.code}/statistics', headers=headers)

    httpx_mock.reset(False)
    assert response.status_code == 200
    assert response.json() == expected_response


@pytest.mark.parametrize(
    'role, search_response, expected_response',
    [
        (
            'collaborator',
            {
                ConfigClass.GREENROOM_ZONE_LABEL: {
                    'files': {
                        'total_count': 5,
                        'total_size': 500,
                    },
                    'activity': {'today_uploaded': 1, 'today_downloaded': 1},
                },
                ConfigClass.CORE_ZONE_LABEL: {
                    'files': {
                        'total_count': 5,
                        'total_size': 500,
                    },
                    'activity': {'today_uploaded': 1, 'today_downloaded': 1},
                },
            },
            {
                'files': {
                    'total_count': 10,
                    'total_size': 1000,
                    'total_per_zone': {
                        ConfigClass.GREENROOM_ZONE_LABEL.lower(): 5,
                        ConfigClass.CORE_ZONE_LABEL.lower(): 5,
                    },
                },
                'activity': {'today_uploaded': 2, 'today_downloaded': 2},
            },
        ),
    ],
)
async def test_statistics_endpoint_returns_search_service_response_limited_to_role_collab(
    role,
    search_response,
    expected_response,
    mocker,
    test_async_client,
    httpx_mock,
    project_factory,
    has_collab_file_permission,
):
    project = project_factory.mock_retrieval_by_code()
    mocker.patch(
        'app.auth.get_current_identity',
        return_value={'role': role, 'username': role, 'realm_roles': [f'{project.code}-{role}']},
    )

    httpx_mock.add_response(
        method='GET',
        url=re.compile(
            rf'^{ConfigClass.SEARCH_SERVICE}/v1/project-files/{project.code}/statistics\?zone=0&parent_path={role}%'
        ),
        json=search_response[ConfigClass.GREENROOM_ZONE_LABEL],
    )
    httpx_mock.add_response(
        method='GET',
        url=re.compile(rf'^{ConfigClass.SEARCH_SERVICE}/v1/project-files/{project.code}/statistics\?zone=1'),
        json=search_response[ConfigClass.GREENROOM_ZONE_LABEL],
    )

    headers = {'Authorization': ''}
    response = await test_async_client.get(f'/v1/project-files/{project.code}/statistics', headers=headers)

    assert response.status_code == 200
    assert response.json() == expected_response


@pytest.mark.parametrize(
    'role, search_response, expected_response',
    [
        (
            'contributor',
            {
                ConfigClass.GREENROOM_ZONE_LABEL: {
                    'files': {
                        'total_count': 5,
                        'total_size': 500,
                    },
                    'activity': {'today_uploaded': 1, 'today_downloaded': 1},
                }
            },
            {
                'files': {
                    'total_count': 5,
                    'total_size': 500,
                    'total_per_zone': {
                        ConfigClass.GREENROOM_ZONE_LABEL.lower(): 5,
                    },
                },
                'activity': {'today_uploaded': 1, 'today_downloaded': 1},
            },
        ),
    ],
)
async def test_statistics_endpoint_returns_search_service_response_limited_contrib(
    role,
    search_response,
    expected_response,
    mocker,
    test_async_client,
    httpx_mock,
    project_factory,
    has_contrib_file_permission,
):
    project = project_factory.mock_retrieval_by_code()
    mocker.patch(
        'app.auth.get_current_identity',
        return_value={'role': role, 'username': role, 'realm_roles': [f'{project.code}-{role}']},
    )

    httpx_mock.add_response(
        method='GET',
        url=re.compile(
            rf'^{ConfigClass.SEARCH_SERVICE}/v1/project-files/{project.code}/statistics\?zone=0&parent_path={role}%'
        ),
        json=search_response[ConfigClass.GREENROOM_ZONE_LABEL],
    )

    headers = {'Authorization': ''}
    response = await test_async_client.get(f'/v1/project-files/{project.code}/statistics', headers=headers)

    assert response.status_code == 200
    assert response.json() == expected_response


@pytest.mark.parametrize('role', ['admin'])
async def test_activity_endpoint_returns_search_service_response_limited_admin(
    role, mocker, test_async_client, httpx_mock, project_factory, has_admin_file_permission
):
    project = project_factory.generate(code='test_project')
    project_factory.mock_retrieval_by_code(project)
    url = (
        f'{ConfigClass.AUTH_SERVICE}authorize?role=admin&resource=project&zone=%2A&operation=view'
        f'&project_code=test_project'
    )
    httpx_mock.add_response(
        method='GET',
        url=url,
        json={'result': {'has_permission': True}},
    )
    mocker.patch(
        'app.auth.get_current_identity',
        return_value={'role': 'member', 'username': 'test', 'realm_roles': [f'{project.code}-{role}']},
    )
    mocker.patch(
        'services.permissions_service.decorators.get_current_identity',
        return_value={'role': 'member', 'username': 'test', 'realm_roles': [f'{project.code}-{role}']},
    )
    expected_response = {
        'data': {
            '2022-01-01': 1,
            '2022-01-02': 0,
            '2022-01-03': 10,
        }
    }
    httpx_mock.add_response(
        method='GET',
        url=re.compile(rf'^{ConfigClass.SEARCH_SERVICE}/v1/project-files/{project.code}/activity'),
        json=expected_response,
    )

    headers = {'Authorization': ''}
    response = await test_async_client.get(f'/v1/project-files/{project.code}/activity', headers=headers)

    httpx_mock.reset(False)
    assert response.status_code == 200

    assert response.json() == expected_response


@pytest.mark.parametrize('role', ['collaborator'])
async def test_activity_endpoint_returns_search_service_response_limited_collab(
    role, test_async_client, httpx_mock, project_factory, has_collab_file_permission, jwt_token_collab
):
    project = project_factory.generate(code='test_project')
    project_factory.mock_retrieval_by_code(project)
    url = (
        f'{ConfigClass.AUTH_SERVICE}authorize?role=collaborator&resource=project&zone=%2A&operation=view'
        f'&project_code=test_project'
    )
    httpx_mock.add_response(
        method='GET',
        url=url,
        json={'result': {'has_permission': True}},
    )
    expected_response = {
        'data': {
            '2022-01-01': 1,
            '2022-01-02': 0,
            '2022-01-03': 10,
        }
    }
    httpx_mock.add_response(
        method='GET',
        url=re.compile(rf'^{ConfigClass.SEARCH_SERVICE}/v1/project-files/{project.code}/activity\?user=test'),
        json=expected_response,
    )

    headers = {'Authorization': ''}
    response = await test_async_client.get(f'/v1/project-files/{project.code}/activity', headers=headers)

    httpx_mock.reset(False)
    assert response.status_code == 200

    assert response.json() == expected_response


@pytest.mark.parametrize('role', ['contributor'])
async def test_activity_endpoint_returns_search_service_response_limited_contrib(
    role, test_async_client, httpx_mock, project_factory, has_contrib_file_permission, jwt_token_contrib
):
    project = project_factory.generate(code='test_project')
    project_factory.mock_retrieval_by_code(project)
    expected_response = {
        'data': {
            '2022-01-01': 1,
            '2022-01-02': 0,
            '2022-01-03': 10,
        }
    }
    url = (
        f'{ConfigClass.AUTH_SERVICE}authorize?role=contributor&resource=project&zone=%2A&operation=view'
        f'&project_code=test_project'
    )
    httpx_mock.add_response(
        method='GET',
        url=url,
        json={'result': {'has_permission': True}},
    )
    httpx_mock.add_response(
        method='GET',
        url=re.compile(rf'^{ConfigClass.SEARCH_SERVICE}/v1/project-files/{project.code}/activity\?user=test'),
        json=expected_response,
    )

    headers = {'Authorization': ''}
    response = await test_async_client.get(f'/v1/project-files/{project.code}/activity', headers=headers)

    httpx_mock.reset(False)
    assert response.status_code == 200

    assert response.json() == expected_response


@pytest.mark.parametrize('role', ['collaborator'])
async def test_activity_endpoint_returns_search_service_response_limited_to_role_invalid_project_permissions(
    role, mocker, test_async_client, fake
):
    project_code = fake.project_code()
    mocker.patch(
        'app.auth.get_current_identity',
        return_value={'role': 'member', 'username': 'test', 'realm_roles': []},
    )
    mocker.patch(
        'services.permissions_service.decorators.get_current_identity',
        return_value={'role': 'member', 'username': 'test', 'realm_roles': []},
    )

    headers = {'Authorization': ''}
    response = await test_async_client.get(f'/v1/project-files/{project_code}/activity', headers=headers)

    assert response.status_code == 403
