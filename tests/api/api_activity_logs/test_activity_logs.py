# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import re

import pytest

from config import ConfigClass

MOCK_DATASET = {
    'creator': 'test',
    'code': 'testprojectdev',
}

MOCK_FOREIGN_DATASET = {
    'creator': 'another_user',
    'code': 'testprojectdev',
}

MOCK_NO_DATASET = {'error': {'code': 'global.not_found', 'details': 'Requested resource is not found'}}


class ProjectObject(object):
    def __init__(self):
        self.code = 'test_project'


class ProjectClient(object):
    def get(self, id_='', code=''):
        return ProjectObject()


@pytest.mark.asyncio
async def test_get_activity_logs_admin_200(test_async_client, httpx_mock, mocker):
    mocker.patch('app.auth.get_current_identity', return_value={'username': 'test'})
    dataset_code = 'testprojectdev'
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.DATASET_SERVICE}datasets/{dataset_code}',
        json=MOCK_DATASET,
    )
    httpx_mock.add_response(
        method='GET',
        url=re.compile(rf'^{ConfigClass.SEARCH_SERVICE}/v1/dataset-activity-logs/.*?container_code={dataset_code}.*$'),
        json={},
    )
    headers = {'Authorization': ''}

    response = await test_async_client.get(f'/v1/activity-logs/{dataset_code}', headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_activity_logs_contrib_200(test_async_client, httpx_mock, mocker):
    mocker.patch('app.auth.get_current_identity', return_value={'username': 'test'})
    dataset_code = 'testprojectdev'
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.DATASET_SERVICE}datasets/{dataset_code}',
        json=MOCK_DATASET,
    )
    httpx_mock.add_response(
        method='GET',
        url=re.compile(rf'^{ConfigClass.SEARCH_SERVICE}/v1/dataset-activity-logs/.*?container_code={dataset_code}.*$'),
        json={},
    )
    headers = {'Authorization': ''}

    response = await test_async_client.get(f'/v1/activity-logs/{dataset_code}', headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_activity_logs_contrib_403_no_permission(test_async_client, httpx_mock, mocker):
    mocker.patch('app.auth.get_current_identity', return_value={'username': 'test'})
    dataset_code = 'testprojectdev'
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.DATASET_SERVICE}datasets/{dataset_code}',
        json=MOCK_FOREIGN_DATASET,
    )
    headers = {'Authorization': ''}

    response = await test_async_client.get(f'/v1/activity-logs/{dataset_code}', headers=headers)
    assert response.status_code == 403
    assert response.json()['result'] == 'No permission for this dataset'


@pytest.mark.asyncio
async def test_get_activity_logs_contrib_403_wrong_dataset_code(test_async_client, httpx_mock, mocker):
    mocker.patch('app.auth.get_current_identity', return_value={'username': 'test'})
    dataset_code = 'testprojectdev'
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.DATASET_SERVICE}datasets/{dataset_code}',
        json=MOCK_NO_DATASET,
        status_code=404,
    )
    headers = {'Authorization': ''}

    response = await test_async_client.get(f'/v1/activity-logs/{dataset_code}', headers=headers)
    assert response.status_code == 400
    assert response.json()['result'] == 'Dataset does not exist'


@pytest.mark.asyncio
async def test_get_project_activity_logs_admin_200(
    test_async_client, httpx_mock, mocker, jwt_token_admin, has_permission_true
):
    project_id = '1234'
    project_code = 'test_project'
    mocker.patch('common.ProjectClient.get', return_value=ProjectClient().get())

    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.SEARCH_SERVICE}/v1/item-activity-logs/?container_code={project_code}',
        json={},
    )
    headers = {'Authorization': ''}

    response = await test_async_client.get(f'/v1/project/activity-logs/{project_id}', headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_project_activity_logs_collaborator_200(
    test_async_client, httpx_mock, mocker, jwt_token_collab, has_collab_file_permission
):
    project_id = '1234'
    project_code = 'test_project'
    mocker.patch('common.ProjectClient.get', return_value=ProjectClient().get())

    url = (
        f'{ConfigClass.AUTH_SERVICE}authorize?role=collaborator&resource=project&zone=%2A&operation=view'
        f'&project_code={project_code}'
    )
    httpx_mock.add_response(
        method='GET',
        url=url,
        json={'result': {'has_permission': True}},
    )

    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.SEARCH_SERVICE}/v1/item-activity-logs/?container_code={project_code}&user=test',
        json={},
    )
    headers = {'Authorization': ''}

    response = await test_async_client.get(f'/v1/project/activity-logs/{project_id}', headers=headers)
    httpx_mock.reset(False)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_project_activity_logs_contributor_200(
    test_async_client, httpx_mock, mocker, jwt_token_contrib, has_contrib_file_permission
):
    project_id = '1234'
    project_code = 'test_project'
    mocker.patch('common.ProjectClient.get', return_value=ProjectClient().get())

    url = (
        f'{ConfigClass.AUTH_SERVICE}authorize?role=contributor&resource=project&zone=%2A&operation=view'
        f'&project_code={project_code}'
    )
    httpx_mock.add_response(
        method='GET',
        url=url,
        json={'result': {'has_permission': True}},
    )

    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.SEARCH_SERVICE}/v1/item-activity-logs/?container_code={project_code}&user=test',
        json={},
    )
    headers = {'Authorization': ''}

    response = await test_async_client.get(f'/v1/project/activity-logs/{project_id}', headers=headers)
    httpx_mock.reset(False)
    assert response.status_code == 200
