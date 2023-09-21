# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from uuid import uuid4

import pytest

from config import ConfigClass

pytestmark = pytest.mark.asyncio


async def test_datasets_get_all_dataset_from_creator_should_return_200(mocker, test_async_client, httpx_mock):
    mocker.patch('app.auth.get_current_identity', return_value={'username': 'any'})
    headers = {'Authorization': ''}
    params = {'creator': 'any'}
    httpx_mock.add_response(
        method='GET', url=f'{ConfigClass.DATASET_SERVICE}datasets/?creator=any', status_code=200, json={}
    )

    response = await test_async_client.get('/v1/datasets/', headers=headers, query_string=params)
    assert response.status_code == 200


async def test_datasets_get_dataset_from_creator_should_return_409_when_current_identity_dont_match(
    mocker, test_async_client
):
    mocker.patch('app.auth.get_current_identity', return_value={'username': 'admin'})
    headers = {'Authorization': ''}
    params = {'creator': 'any'}

    response = await test_async_client.get('/v1/datasets/', headers=headers, query_string=params)
    assert response.status_code == 403
    assert response.json() == {'err_msg': 'No permissions'}


async def test_datasets_get_dataset_by_identifier_should_return_200(mocker, test_async_client, httpx_mock):
    mocker.patch('app.auth.get_current_identity', return_value={'username': 'admin'})
    headers = {'Authorization': ''}
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.DATASET_SERVICE}datasets/identifier',
        status_code=200,
        json={'creator': 'admin'},
    )

    response = await test_async_client.get('/v1/datasets/identifier', headers=headers)
    assert response.status_code == 200


async def test_datasets_get_dataset_by_identifier_should_return_409_when_current_identity_dont_match(
    mocker, test_async_client, httpx_mock
):
    mocker.patch('app.auth.get_current_identity', return_value={'username': 'admin'})
    headers = {'Authorization': ''}
    httpx_mock.add_response(
        method='GET', url=f'{ConfigClass.DATASET_SERVICE}datasets/identifier', status_code=200, json={'creator': 'any'}
    )

    response = await test_async_client.get('/v1/datasets/identifier', headers=headers)
    assert response.status_code == 403
    assert response.json() == {'code': 403, 'error_msg': 'Permission denied', 'result': ''}


async def test_datasets_get_dataset_by_identifier_should_return_dataset_service_response(
    mocker, test_async_client, httpx_mock
):
    mocker.patch('app.auth.get_current_identity', return_value={'username': 'admin'})
    headers = {'Authorization': ''}
    httpx_mock.add_response(
        method='GET', url=f'{ConfigClass.DATASET_SERVICE}datasets/identifier', status_code=500, json={'error': 'any'}
    )

    response = await test_async_client.get('/v1/datasets/identifier', headers=headers)
    assert response.status_code == 500
    assert response.json() == {'error': 'any'}


async def test_datasets_post_dataset_should_return_200(mocker, test_async_client, httpx_mock):
    mocker.patch('app.auth.get_current_identity', return_value={'username': 'any'})
    headers = {'Authorization': ''}
    params = {'creator': 'any'}
    httpx_mock.add_response(method='POST', url=f'{ConfigClass.DATASET_SERVICE}datasets/', status_code=200, json={})

    response = await test_async_client.post('/v1/datasets/', headers=headers, json=params)
    assert response.json() == {}
    assert response.status_code == 200


async def test_datasets_post_dataset_when_jwt_username_and_dataset_creator_are_different_should_return_403(
    mocker, test_async_client, httpx_mock
):
    mocker.patch('app.auth.get_current_identity', return_value={'username': 'any'})
    headers = {'Authorization': ''}
    params = {'creator': 'another'}

    response = await test_async_client.post('/v1/datasets/', headers=headers, json=params)
    assert response.status_code == 403


async def test_dataset_get_version_should_build_correct_url(mocker, test_async_client, httpx_mock):
    mocker.patch('app.auth.get_current_identity', return_value={'username': 'any'})
    headers = {'Authorization': ''}
    params = {'order_by': 'asc'}
    dataset_id = str(uuid4())
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.DATASET_SERVICE}dataset/versions?order_by=asc&dataset_id={dataset_id}',
        status_code=200,
        json={},
    )

    response = await test_async_client.get(f'/v1/dataset/{dataset_id}/versions', headers=headers, query_string=params)
    assert response.json() == {}
    assert response.status_code == 200
