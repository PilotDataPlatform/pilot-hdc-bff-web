# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import re
from uuid import uuid4

from config import ConfigClass


async def test_list_spaces_calls_kg_service(test_async_client, httpx_mock):
    headers = {'Authorization': 'Bearer token'}
    expected_result = {'result': [{'name': 'hdc-myspace'}, {'name': 'myspace'}]}
    httpx_mock.add_response(
        method='GET', url=f'{ConfigClass.KG_SERVICE}/v1/spaces/', json=expected_result, match_headers=headers
    )

    response = await test_async_client.get('/v1/kg/spaces', headers=headers)

    assert response.status_code == 200
    assert response.json() == expected_result


async def test_get_space_by_id_calls_kg_service(test_async_client, httpx_mock):
    space = 'myspace'
    expected_result = {
        'name': 'myspace',
        'identifier': 'myspace',
        'autorelease': False,
        'clientSpace': False,
        'deferCache': False,
    }
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.KG_SERVICE}/v1/spaces/{space}',
        json=expected_result,
    )

    response = await test_async_client.get(f'/v1/kg/spaces/{space}')

    assert response.status_code == 200
    assert response.json() == expected_result


async def test_create_space_calls_kg_service(test_async_client, httpx_mock):
    httpx_mock.add_response(method='POST', url=f'{ConfigClass.KG_SERVICE}/v1/spaces/create', json={}, status_code=201)

    response = await test_async_client.post('/v1/kg/spaces/create')

    assert response.status_code == 201


async def test_create_space_for_project_calls_kg_service(
    test_async_client, httpx_mock, jwt_token_admin, has_permission_true
):
    headers = {'Authorization': 'Bearer token'}
    httpx_mock.add_response(
        method='POST',
        url=f'{ConfigClass.KG_SERVICE}/v1/spaces/create/project/test',
        json={},
        status_code=201,
        match_headers=headers,
    )

    response = await test_async_client.post('/v1/kg/spaces/create/project/test', json={}, headers=headers)

    assert response.status_code == 201


async def test_create_space_for_dataset_calls_kg_service(test_async_client, httpx_mock):
    headers = {'Authorization': 'Bearer token'}
    httpx_mock.add_response(
        method='POST',
        url=f'{ConfigClass.KG_SERVICE}/v1/spaces/create/dataset/test',
        json={},
        status_code=201,
        match_headers=headers,
    )

    response = await test_async_client.post('/v1/kg/spaces/create/dataset/test', json={}, headers=headers)

    assert response.status_code == 201


async def test_list_metadata_calls_kg_service(test_async_client, httpx_mock):
    expected_result = {
        'result': [
            {
                'creator': '0d3137ad-ff53-46dc-b68e-b781edc3e37b',
                'data': {'http://schema.org/name': 'Matvey', 'http://schema.org/surname': 'Loshakov'},
                'id': '9bd75916-4dce-49f6-a70b-878cc7f36cf7',
                'revision': 'rev',
                'space': 'myspace',
                'type': ['https://openminds.ebrains.eu/core/person'],
            },
            {
                'creator': '0d3137ad-ff53-46dc-b68e-b781edc3e37b',
                'data': {'http://schema.org/name': 'Also Matvey', 'http://schema.org/surname': 'Loshakov Again'},
                'id': 'b5817f36-da1e-44a2-81ed-3d769450eb65',
                'revision': 'rev',
                'space': 'myspace',
                'type': ['https://openminds.ebrains.eu/core/person'],
            },
        ]
    }
    headers = {'Authorization': 'Bearer token'}
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.KG_SERVICE}/v1/metadata/',
        json=expected_result,
    )

    response = await test_async_client.get('/v1/kg/metadata', headers=headers)

    assert response.status_code == 200
    assert response.json() == expected_result


async def test_get_metadata_by_id_calls_kg_service(test_async_client, httpx_mock):
    expected_result = {
        'creator': '0d3137ad-ff53-46dc-b68e-b781edc3e37b',
        'data': {'http://schema.org/name': 'Matvey', 'http://schema.org/surname': 'Loshakov'},
        'id': '9bd75916-4dce-49f6-a70b-878cc7f36cf7',
        'revision': 'rev',
        'space': 'myspace',
        'type': ['https://openminds.ebrains.eu/core/person'],
    }
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.KG_SERVICE}/v1/metadata/9bd75916-4dce-49f6-a70b-878cc7f36cf7',
        json=expected_result,
    )

    response = await test_async_client.get('/v1/kg/metadata/9bd75916-4dce-49f6-a70b-878cc7f36cf7')

    assert response.status_code == 200
    assert response.json() == expected_result


async def test_upload_metadata_calls_kg_service(test_async_client, httpx_mock):
    expected_result = {
        'creator': '0d3137ad-ff53-46dc-b68e-b781edc3e37b',
        'data': {'http://schema.org/name': 'Matvey', 'http://schema.org/surname': 'Loshakov'},
        'id': '9bd75916-4dce-49f6-a70b-878cc7f36cf7',
        'revision': 'rev',
        'space': 'myspace',
        'type': ['https://openminds.ebrains.eu/core/person'],
    }
    headers = {'Authorization': 'Bearer token'}
    httpx_mock.add_response(
        method='POST',
        url=f'{ConfigClass.KG_SERVICE}/v1/metadata/upload',
        json=expected_result,
    )

    response = await test_async_client.post(
        '/v1/kg/metadata/upload',
        json={
            '@type': 'https://openminds.ebrains.eu/core/person',
            'http://schema.org/name': 'Matvey',
            'http://schema.org/surname': 'Loshakov',
        },
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == expected_result


async def test_update_metadata_calls_kg_service(test_async_client, httpx_mock):
    metadata_id = str(uuid4())
    expected_result = {
        'creator': '0d3137ad-ff53-46dc-b68e-b781edc3e37b',
        'data': {'http://schema.org/name': 'Matvey', 'http://schema.org/surname': 'Loshakov'},
        'id': '9bd75916-4dce-49f6-a70b-878cc7f36cf7',
        'revision': 'rev',
        'space': 'myspace',
        'type': ['https://openminds.ebrains.eu/core/person'],
    }
    headers = {'Authorization': 'Bearer token'}
    httpx_mock.add_response(
        method='PUT',
        url=f'{ConfigClass.KG_SERVICE}/v1/metadata/update/{metadata_id}',
        json=expected_result,
    )

    response = await test_async_client.put(
        f'/v1/kg/metadata/update/{metadata_id}',
        json={
            '@type': 'https://openminds.ebrains.eu/core/person',
            'http://schema.org/name': 'Matvey',
            'http://schema.org/surname': 'Loshakov',
        },
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == expected_result


async def test_list_users_calls_kg_service(test_async_client, httpx_mock):
    expected_result = {
        'users': [
            {
                'id': '580597af-7928-4b69-a547-3ebfb9f1b010',
                'mitreId': '5089721700637136',
                'username': 'mloshakov',
                'firstName': 'Matvey',
                'lastName': 'Loshakov',
                'biography': '',
                'avatar': '',
                'active': True,
            }
        ],
        'units': [],
        'groups': [],
    }
    headers = {'Authorization': 'Bearer token'}
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.KG_SERVICE}/v1/users/myspace',
        json=expected_result,
    )

    response = await test_async_client.get('/v1/kg/users/myspace', headers=headers)

    assert response.status_code == 200
    assert response.json() == expected_result


async def test_add_user_calls_kg_service(test_async_client, httpx_mock, jwt_token_admin, has_permission_true):
    project_id = str(uuid4())
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*project.*'),
        json={},
    )
    httpx_mock.add_response(
        method='POST',
        url=f'{ConfigClass.KG_SERVICE}/v1/users/{project_id}/mloshakov',
    )

    response = await test_async_client.post(f'/v1/kg/users/{project_id}/mloshakov')

    assert response.status_code == 200


async def test_delete_user_calls_kg_service(test_async_client, httpx_mock, jwt_token_admin, has_permission_true):
    project_id = str(uuid4())
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*project.*'),
        json={},
    )
    httpx_mock.add_response(
        method='DELETE',
        url=f'{ConfigClass.KG_SERVICE}/v1/users/{project_id}/mloshakov',
    )

    response = await test_async_client.delete(f'/v1/kg/users/{project_id}/mloshakov')

    assert response.status_code == 200


async def test_update_user_calls_kg_service(test_async_client, httpx_mock, jwt_token_admin, has_permission_true):
    project_id = str(uuid4())
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*project.*'),
        json={},
    )
    httpx_mock.add_response(
        method='PUT',
        url=f'{ConfigClass.KG_SERVICE}/v1/users/{project_id}/mloshakov',
    )

    response = await test_async_client.put(f'/v1/kg/users/{project_id}/mloshakov')

    assert response.status_code == 200
