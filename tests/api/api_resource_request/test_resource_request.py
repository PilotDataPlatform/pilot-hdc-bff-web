# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from uuid import uuid4

import pytest

from config import ConfigClass

RESOURCE_REQUEST = {
    'project_id': str(uuid4()),
    'user_id': str(uuid4()),
    'username': 'test@test.com',
    'email': 'test@test.com',
    'requested_for': 'SuperSet',
    'completed_at': '2022-07-05T14:27:14.834812+00:00',
    'id': str(uuid4()),
    'project': {'code': 'testproject'},
    'vm_connections': {},
}

PROJECT = {
    'id': RESOURCE_REQUEST['project_id'],
    'name': 'testproject',
    'code': 'test_project',
}

USER = {
    'id': RESOURCE_REQUEST['user_id'],
    'email': 'test@test.com',
    'name': 'test',
    'username': 'test',
}


def test_get_request_200(test_client, httpx_mock, jwt_token_admin, has_permission_true):
    request_id = RESOURCE_REQUEST['id']
    httpx_mock.add_response(
        method='GET',
        url=ConfigClass.PROJECT_SERVICE + f'/v1/resource-requests/{request_id}',
        json=RESOURCE_REQUEST,
        status_code=200,
    )
    response = test_client.get(f'/v1/resource-request/{request_id}')
    assert response.status_code == 200


def test_get_request_403(test_client, httpx_mock, jwt_token_contrib, has_permission_false):
    request_id = RESOURCE_REQUEST['id']
    response = test_client.get(f'/v1/resource-request/{request_id}', params={'project_code': 'test_project'})
    assert response.status_code == 403


def test_delete_request_200(test_client, httpx_mock, jwt_token_admin, has_permission_true):
    request_id = RESOURCE_REQUEST['id']
    httpx_mock.add_response(
        method='DELETE',
        url=ConfigClass.PROJECT_SERVICE + f'/v1/resource-requests/{request_id}',
        json=RESOURCE_REQUEST,
        status_code=204,
    )
    response = test_client.delete(f'/v1/resource-request/{request_id}/')
    assert response.status_code == 200


def test_delete_request_400(test_client, httpx_mock, jwt_token_admin, has_permission_true):
    request_id = RESOURCE_REQUEST['id']
    httpx_mock.add_response(
        method='DELETE',
        url=ConfigClass.PROJECT_SERVICE + f'/v1/resource-requests/{request_id}',
        json=RESOURCE_REQUEST,
        status_code=400,
    )
    response = test_client.delete(f'/v1/resource-request/{request_id}/')
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_put_request_complete_200(
    test_async_client, requests_mocker, httpx_mock, jwt_token_admin, has_permission_true
):
    request_id = RESOURCE_REQUEST['id']
    project_id = RESOURCE_REQUEST['project_id']
    user_id = RESOURCE_REQUEST['user_id']

    httpx_mock.add_response(
        method='GET', url=ConfigClass.PROJECT_SERVICE + f'/v1/projects/{project_id}', json=PROJECT, status_code=200
    )

    httpx_mock.add_response(
        method='GET',
        url=ConfigClass.PROJECT_SERVICE + f'/v1/resource-requests/{request_id}',
        json=RESOURCE_REQUEST,
        status_code=200,
    )

    httpx_mock.add_response(
        method='PATCH',
        url=ConfigClass.PROJECT_SERVICE + f'/v1/resource-requests/{request_id}',
        json=RESOURCE_REQUEST,
        status_code=200,
    )

    httpx_mock.add_response(
        method='GET',
        url=ConfigClass.AUTH_SERVICE + f'admin/user?user_id={user_id}&exact=true',
        json={'result': USER},
        status_code=200,
    )

    httpx_mock.add_response(
        method='POST', url=ConfigClass.NOTIFY_SERVICE + '/v1/email/', json={'result': 'success'}, status_code=200
    )

    response = await test_async_client.put(f'/v1/resource-request/{request_id}/complete')
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_put_request_complete_500(
    test_async_client, requests_mocker, httpx_mock, jwt_token_admin, has_permission_true
):
    request_id = RESOURCE_REQUEST['id']
    user_id = RESOURCE_REQUEST['user_id']

    httpx_mock.add_response(
        method='GET',
        url=ConfigClass.PROJECT_SERVICE + f'/v1/resource-requests/{request_id}',
        json=RESOURCE_REQUEST,
        status_code=200,
    )

    httpx_mock.add_response(
        method='PATCH',
        url=ConfigClass.PROJECT_SERVICE + f'/v1/resource-requests/{request_id}',
        json=RESOURCE_REQUEST,
        status_code=200,
    )

    httpx_mock.add_response(
        method='GET',
        url=ConfigClass.AUTH_SERVICE + f'admin/user?user_id={user_id}&exact=true',
        json={'result': USER},
        status_code=500,
    )

    response = await test_async_client.put(f'/v1/resource-request/{request_id}/complete')
    assert response.status_code == 500


@pytest.mark.asyncio
async def test_post_request_query_200(test_async_client, httpx_mock, jwt_token_admin, has_permission_true):

    result = {'num_of_pages': 1, 'page': 0, 'total': 1, 'result': [RESOURCE_REQUEST]}
    url = ConfigClass.PROJECT_SERVICE + (
        '/v1/resource-requests/?page=0&page_size=25&sort_by=requested_at&sort_order=asc&username='
    )
    httpx_mock.add_response(method='GET', url=url, json=result, status_code=200)

    payload = {
        'page': 0,
        'page_size': 25,
    }
    response = await test_async_client.post('/v1/resource-requests/query', json=payload)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_post_request_query_filter_200(test_async_client, httpx_mock, jwt_token_admin, has_permission_true):

    result = {'num_of_pages': 1, 'page': 0, 'total': 1, 'result': [RESOURCE_REQUEST]}
    url = ConfigClass.PROJECT_SERVICE + (
        '/v1/resource-requests/?page=0&page_size=25&sort_by=requested_at'
        '&sort_order=asc&username=test%25&email=a%40test.com%25'
    )
    httpx_mock.add_response(method='GET', url=url, json=result, status_code=200)

    payload = {
        'page': 0,
        'page_size': 25,
        'username': 'test',
        'email': 'a@test.com',
    }
    response = await test_async_client.post('/v1/resource-requests/query', json=payload)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_post_request_query_422(test_async_client, httpx_mock, jwt_token_admin, has_permission_true):

    result = {'num_of_pages': 1, 'page': 0, 'total': 1, 'result': [RESOURCE_REQUEST]}
    url = ConfigClass.PROJECT_SERVICE + (
        '/v1/resource-requests/?page=0&page_size=25&sort_by=requested_at&sort_order=asc&username='
    )
    httpx_mock.add_response(method='GET', url=url, json=result, status_code=422)

    payload = {
        'page': 0,
        'page_size': 25,
    }
    response = await test_async_client.post('/v1/resource-requests/query', json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_post_request_query_contrib_200(test_async_client, httpx_mock, jwt_token_contrib):
    payload = {
        'page': 0,
        'page_size': 25,
        'project_code': 'testproject',
    }
    response = await test_async_client.post('/v1/resource-requests/query', json=payload)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_post_request_create_200(test_async_client, httpx_mock, jwt_token_contrib, has_permission_true):

    project_id = RESOURCE_REQUEST['project_id']

    url = ConfigClass.PROJECT_SERVICE + '/v1/resource-requests/'
    httpx_mock.add_response(method='POST', url=url, json=RESOURCE_REQUEST, status_code=200)

    httpx_mock.add_response(
        method='GET',
        url=ConfigClass.AUTH_SERVICE + f'admin/user?username={ConfigClass.RESOURCE_REQUEST_ADMIN}',
        json={'result': USER},
        status_code=200,
    )

    httpx_mock.add_response(
        method='POST', url=ConfigClass.NOTIFY_SERVICE + '/v1/email/', json={'result': 'success'}, status_code=200
    )

    payload = {
        'user_id': RESOURCE_REQUEST['user_id'],
        'project_id': project_id,
        'request_for': 'SuperSet',
        'message': 'Test',
    }
    response = await test_async_client.post('/v1/resource-requests', json=payload)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_post_request_create_403(test_async_client, httpx_mock, jwt_token_contrib):

    different_project = PROJECT.copy()
    different_project['id'] = str(uuid4())
    different_project['code'] = 'different_project'
    project_id = different_project['id']
    httpx_mock.add_response(
        method='GET',
        url=ConfigClass.PROJECT_SERVICE + f'/v1/projects/{project_id}',
        json=different_project,
        status_code=200,
    )

    payload = {
        'user_id': RESOURCE_REQUEST['user_id'],
        'project_id': project_id,
        'request_for': 'SuperSet',
        'message': 'Test',
    }
    response = await test_async_client.post('/v1/resource-requests', json=payload)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_post_request_create_500(test_async_client, httpx_mock, jwt_token_contrib, has_permission_true):
    project_id = RESOURCE_REQUEST['project_id']

    url = ConfigClass.PROJECT_SERVICE + '/v1/resource-requests/'
    httpx_mock.add_response(method='POST', url=url, json=RESOURCE_REQUEST, status_code=500)

    payload = {
        'user_id': RESOURCE_REQUEST['user_id'],
        'project_id': project_id,
        'request_for': 'SuperSet',
        'message': 'Test',
    }
    response = await test_async_client.post('/v1/resource-requests', json=payload)
    assert response.status_code == 500


def test_patch_update_request_200(test_client, httpx_mock, jwt_token_contrib, has_permission_true):
    request_id = RESOURCE_REQUEST['id']

    httpx_mock.add_response(
        method='PATCH',
        url=ConfigClass.PROJECT_SERVICE + f'/v1/resource-requests/{request_id}',
        json=RESOURCE_REQUEST,
        status_code=200,
    )
    httpx_mock.add_response(
        method='POST', url=ConfigClass.WORKSPACE_SERVICE + 'guacamole/permission', json={}, status_code=200
    )
    httpx_mock.add_response(
        method='GET',
        url=ConfigClass.PROJECT_SERVICE + f'/v1/resource-requests/{request_id}',
        json=RESOURCE_REQUEST,
        status_code=200,
    )

    payload = {
        'connections': [
            {
                'name': 'vm_name',
                'permissions': ['READ'],
                'operation': 'add',
            }
        ],
        'container_code': 'test_project',
    }
    response = test_client.patch(f'/v1/resource-request/{request_id}/', json=payload)
    assert response.status_code == 200


def test_patch_update_request_project_error_500(test_client, httpx_mock, jwt_token_contrib, has_permission_true):
    request_id = RESOURCE_REQUEST['id']

    httpx_mock.add_response(
        method='PATCH',
        url=ConfigClass.PROJECT_SERVICE + f'/v1/resource-requests/{request_id}',
        json=RESOURCE_REQUEST,
        status_code=500,
    )
    httpx_mock.add_response(
        method='POST', url=ConfigClass.WORKSPACE_SERVICE + 'guacamole/permission', json={}, status_code=200
    )
    httpx_mock.add_response(
        method='GET',
        url=ConfigClass.PROJECT_SERVICE + f'/v1/resource-requests/{request_id}',
        json=RESOURCE_REQUEST,
        status_code=200,
    )

    payload = {
        'connections': [
            {
                'name': 'vm_name',
                'permissions': ['READ'],
                'operation': 'add',
            }
        ],
        'container_code': 'test_project',
    }
    response = test_client.patch(f'/v1/resource-request/{request_id}/', json=payload)
    assert response.status_code == 500


def test_patch_update_request_workspace_error_500(test_client, httpx_mock, jwt_token_contrib, has_permission_true):
    request_id = RESOURCE_REQUEST['id']

    httpx_mock.add_response(
        method='POST', url=ConfigClass.WORKSPACE_SERVICE + 'guacamole/permission', json={}, status_code=500
    )
    httpx_mock.add_response(
        method='GET',
        url=ConfigClass.PROJECT_SERVICE + f'/v1/resource-requests/{request_id}',
        json=RESOURCE_REQUEST,
        status_code=200,
    )

    payload = {
        'connections': [
            {
                'name': 'vm_name',
                'permissions': ['READ'],
                'operation': 'add',
            }
        ],
        'container_code': 'test_project',
    }
    response = test_client.patch(f'/v1/resource-request/{request_id}/', json=payload)
    assert response.status_code == 500


def test_patch_update_request_no_name_400(test_client, httpx_mock, jwt_token_contrib, has_permission_true):
    request_id = RESOURCE_REQUEST['id']
    payload = {
        'connections': [
            {
                'permissions': ['READ'],
                'operation': 'add',
            }
        ],
        'container_code': 'test_project',
    }
    response = test_client.patch(f'/v1/resource-request/{request_id}/', json=payload)
    assert response.status_code == 400


def test_patch_update_request_bad_permission_400(test_client, httpx_mock, jwt_token_contrib, has_permission_true):
    request_id = RESOURCE_REQUEST['id']

    payload = {
        'connections': [
            {
                'name': 'vm_name',
                'permissions': ['BAD'],
                'operation': 'add',
            }
        ],
        'container_code': 'test_project',
    }
    response = test_client.patch(f'/v1/resource-request/{request_id}/', json=payload)
    assert response.status_code == 400


def test_patch_update_request_bad_operastion_400(test_client, httpx_mock, jwt_token_contrib, has_permission_true):
    request_id = RESOURCE_REQUEST['id']

    payload = {
        'connections': [
            {
                'name': 'vm_name',
                'permissions': ['READ'],
                'operation': 'bad',
            }
        ],
        'container_code': 'test_project',
    }
    response = test_client.patch(f'/v1/resource-request/{request_id}/', json=payload)
    assert response.status_code == 400
