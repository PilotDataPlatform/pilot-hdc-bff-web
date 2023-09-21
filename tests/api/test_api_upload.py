# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import re

import pytest

from config import ConfigClass

MOCK_FILE = {'result': [{'name': 'test'}]}


@pytest.fixture
def get_file_entity(requests_mocker):
    requests_mocker.get(
        ConfigClass.METADATA_SERVICE + 'item/test_item_id',
        json={
            'code': 200,
            'error_msg': '',
            'page': 0,
            'total': 0,
            'num_of_pages': 1,
            'result': {
                'id': 'item-id',
                'parent': 'parent-id',
                'parent_path': 'testuser',
                'restore_path': None,
                'status': False,
                'type': 'file',
                'zone': 0,
                'name': 'fake_file',
                'size': 0,
                'owner': 'testuser',
                'container_code': 'test_project',
                'container_type': 'project',
                'created_time': '2022-04-13 18:17:51.008212',
                'last_updated_time': '2022-04-13 18:17:51.008227',
            },
        },
    )


@pytest.mark.asyncio
async def test_proxy_pre_upload_successful(
    test_async_client, requests_mocker, httpx_mock, jwt_token_admin, get_file_entity, has_permission_true
):

    project_code = 'test_project'
    payload = {
        'current_folder_node': 'test_folder',
        'parent_folder_id': 'test_item_id',
        'project_code': 'test_project',
        'operator': 'test_user',
        'data': [],
        'job_type': 'AS_FILE',
        'zone': 'greenroom',
    }

    httpx_mock.add_response(method='POST', url=ConfigClass.UPLOAD_SERVICE + '/v1/files/jobs', json={'result': {}})
    headers = {'Authorization': ''}
    response = await test_async_client.post(f'/v1/project/{project_code}/files', json=payload, headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_proxy_pre_upload_fail_with_tag(
    test_async_client, requests_mocker, httpx_mock, jwt_token_admin, get_file_entity
):
    url = (
        ConfigClass.AUTH_SERVICE
        + 'authorize?role=platform_admin&resource=file_any&zone=greenroom&operation=upload&project_code=test_project'
    )
    httpx_mock.add_response(method='GET', url=url, json={'result': {'has_permission': True}})
    url = (
        ConfigClass.AUTH_SERVICE
        + 'authorize?role=platform_admin&resource=file_any&zone=greenroom&operation=annotate&project_code=test_project'
    )
    httpx_mock.add_response(method='GET', url=url, json={'result': {'has_permission': False}})

    project_code = 'test_project'
    payload = {
        'current_folder_node': 'test_folder',
        'parent_folder_id': 'test_item_id',
        'project_code': 'test_project',
        'operator': 'test_user',
        'data': [],
        'job_type': 'AS_FILE',
        'zone': 'greenroom',
        'folder_tags': ['test_tag'],
    }

    headers = {'Authorization': ''}
    response = await test_async_client.post(f'/v1/project/{project_code}/files', json=payload, headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_proxy_pre_upload_successfulwith_tag(
    test_async_client, requests_mocker, httpx_mock, jwt_token_admin, get_file_entity, has_permission_true
):

    project_code = 'test_project'
    payload = {
        'current_folder_node': 'test_folder',
        'parent_folder_id': 'test_item_id',
        'project_code': 'test_project',
        'operator': 'test_user',
        'data': [],
        'job_type': 'AS_FILE',
        'zone': 'greenroom',
        'folder_tags': ['test_tag'],
    }

    httpx_mock.add_response(method='POST', url=ConfigClass.UPLOAD_SERVICE + '/v1/files/jobs', json={'result': {}})
    headers = {'Authorization': ''}
    response = await test_async_client.post(f'/v1/project/{project_code}/files', json=payload, headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_proxy_pre_upload_409(
    test_async_client, requests_mocker, httpx_mock, jwt_token_admin, get_file_entity, has_permission_true
):

    project_code = 'test_project'
    payload = {
        'current_folder_node': 'test_folder',
        'parent_folder_id': 'test_item_id',
        'project_code': 'test_project',
        'operator': 'test_user',
        'data': [],
        'job_type': 'AS_FILE',
    }

    response_json = {'error_msg': 'error when pre upload', 'result': ''}
    httpx_mock.add_response(
        method='POST', url=ConfigClass.UPLOAD_SERVICE + '/v1/files/jobs', json=response_json, status_code=409
    )
    headers = {'Authorization': ''}
    response = await test_async_client.post(f'/v1/project/{project_code}/files', json=payload, headers=headers)

    assert response.status_code == 409
    assert response.json().get('error_msg') == 'error when pre upload'


@pytest.mark.asyncio
async def test_proxy_chunk_presigned_successful(test_async_client, requests_mocker, httpx_mock, jwt_token_admin):
    project_code = 'test_project'
    key = 'filepath'
    upload_id = 'test_upload_id'
    chunk_number = 1

    httpx_mock.add_response(
        method='GET',
        url=(
            f'{ConfigClass.UPLOAD_SERVICE}/v1/files/chunks/presigned?'
            f'bucket=gr-{project_code}&key={key}&upload_id={upload_id}&chunk_number={chunk_number}'
        ),
        json={'result': {}},
    )
    headers = {'Authorization': ''}
    response = await test_async_client.get(
        (
            f'/v1/project/{project_code}/files/chunks/presigned?'
            f'key={key}&upload_id={upload_id}&chunk_number={chunk_number}'
        ),
        headers=headers,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_proxy_get_resumable_successful(
    test_async_client, requests_mocker, httpx_mock, jwt_token_admin, get_file_entity, has_permission_true
):
    project_code = 'test_project'
    parent_path = 'filepath'
    item_name = 'test.txt'
    file_path = f'{parent_path}/{item_name}'
    upload_id = 'test_upload_id'
    item_id = 'test_item_id'

    httpx_mock.add_response(
        method='POST',
        url=ConfigClass.UPLOAD_SERVICE + '/v1/files/resumable',
        json={},
    )

    headers = {'Authorization': ''}
    response = await test_async_client.post(
        (f'/v1/project/{project_code}/files/resumable'),
        json={'object_infos': [{'resumable_id': upload_id, 'item_id': item_id, 'object_path': file_path}]},
        headers=headers,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_proxy_get_resumable_fail(
    test_async_client, requests_mocker, httpx_mock, jwt_token_admin, get_file_entity, has_permission_true
):
    project_code = 'test_project'
    parent_path = 'filepath'
    item_name = 'test.txt'
    file_path = f'{parent_path}/{item_name}'
    upload_id = 'test_upload_id'
    item_id = 'test_item_id'

    headers = {'Authorization': ''}
    response = await test_async_client.post(
        (f'/v1/project/{project_code}/files/resumable'),
        json={'object_infos': [{'resumable_id': upload_id, 'item_id': item_id, 'object_path': file_path}]},
        headers=headers,
    )
    assert response.status_code == 500


@pytest.mark.asyncio
async def test_proxy_list_resumable_successful(test_async_client, requests_mocker, httpx_mock, jwt_token_admin):
    project_code = 'test_project'

    url = re.compile(r'^' + ConfigClass.METADATA_SERVICE + 'items/search/.*$')
    httpx_mock.add_response(
        url=url,
        method='GET',
        json=MOCK_FILE,
    )

    headers = {'Authorization': ''}
    response = await test_async_client.get(
        (f'/v1/project/{project_code}/files/resumable'),
        headers=headers,
    )
    assert response.status_code == 200
