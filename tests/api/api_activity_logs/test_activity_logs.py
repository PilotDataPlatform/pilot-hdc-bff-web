# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import re

from app.components.user.models import CurrentUser
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


async def test_get_activity_logs_admin_200(test_async_client, httpx_mock, mocker):
    mocker.patch('app.auth.get_current_identity', return_value=CurrentUser({'username': 'test'}))
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


async def test_get_activity_logs_contrib_200(test_async_client, httpx_mock, mocker):
    mocker.patch('app.auth.get_current_identity', return_value=CurrentUser({'username': 'test'}))
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


async def test_get_activity_logs_contrib_403_no_permission(test_async_client, httpx_mock, mocker):
    mocker.patch('app.auth.get_current_identity', return_value=CurrentUser({'username': 'test'}))
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


async def test_get_activity_logs_contrib_404_wrong_dataset_code(test_async_client, httpx_mock, mocker):
    mocker.patch('app.auth.get_current_identity', return_value=CurrentUser({'username': 'test'}))
    dataset_code = 'testprojectdev'
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.DATASET_SERVICE}datasets/{dataset_code}',
        json=MOCK_NO_DATASET,
        status_code=404,
    )
    headers = {'Authorization': ''}

    response = await test_async_client.get(f'/v1/activity-logs/{dataset_code}', headers=headers)
    assert response.status_code == 404
    assert response.json()['result'] == 'Dataset does not exist'


async def test_get_project_activity_logs_admin_200(
    test_async_client, httpx_mock, jwt_token_admin, has_permission_true, project_factory
):
    project = project_factory.mock_retrieval_by_id()

    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.SEARCH_SERVICE}/v1/item-activity-logs/?container_code={project.code}',
        json={},
    )
    headers = {'Authorization': ''}

    response = await test_async_client.get(f'/v1/project/activity-logs/{project.id}', headers=headers)
    assert response.status_code == 200


async def test_get_project_activity_logs_collaborator_200(
    test_async_client, httpx_mock, jwt_token_collab, has_collab_file_permission, project_factory
):
    project = project_factory.generate(code='test_project')
    project_factory.mock_retrieval_by_id(project)

    url = (
        f'{ConfigClass.AUTH_SERVICE}authorize?role=collaborator&resource=project&zone=%2A&operation=view'
        f'&project_code={project.code}'
    )
    httpx_mock.add_response(
        method='GET',
        url=url,
        json={'result': {'has_permission': True}},
    )

    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.SEARCH_SERVICE}/v1/item-activity-logs/?container_code={project.code}&user=test',
        json={},
    )
    headers = {'Authorization': ''}

    response = await test_async_client.get(f'/v1/project/activity-logs/{project.id}', headers=headers)
    httpx_mock.reset(False)
    assert response.status_code == 200


async def test_get_project_activity_logs_contributor_200(
    test_async_client, httpx_mock, jwt_token_contrib, has_contrib_file_permission, project_factory
):
    project = project_factory.generate(code='test_project')
    project_factory.mock_retrieval_by_id(project)

    url = (
        f'{ConfigClass.AUTH_SERVICE}authorize?role=contributor&resource=project&zone=%2A&operation=view'
        f'&project_code={project.code}'
    )
    httpx_mock.add_response(
        method='GET',
        url=url,
        json={'result': {'has_permission': True}},
    )

    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.SEARCH_SERVICE}/v1/item-activity-logs/?container_code={project.code}&user=test',
        json={},
    )
    headers = {'Authorization': ''}

    response = await test_async_client.get(f'/v1/project/activity-logs/{project.id}', headers=headers)
    httpx_mock.reset(False)
    assert response.status_code == 200
