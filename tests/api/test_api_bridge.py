# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import pytest
from redis.asyncio import Redis
from redis.exceptions import RedisError

from config import ConfigClass
from services.bridge import get_bridge_service


@pytest.mark.parametrize(
    'entity,url',
    [
        ('project', f'{ConfigClass.PROJECT_SERVICE}/v1/projects'),
        ('dataset', f'{ConfigClass.DATASET_SERVICE}datasets'),
    ],
)
async def test_add_visits_returns_success(entity, url, mocker, test_async_client, httpx_mock):
    mocker.patch('app.auth.get_current_identity', return_value={'username': 'admin'})
    httpx_mock.add_response(
        method='GET',
        url=f'{url}/any',
        status_code=200,
        json={'code': 'any'},
    )
    params = {'entity': entity, 'code': 'any'}

    response = await test_async_client.post('/v1/visits', json=params)
    assert response.status_code == 200
    assert response.json() == {'code': 200, 'result': 'success'}
    bridge_service = await get_bridge_service()
    code = (await bridge_service.REDIS.lrange(f'{entity}:admin:visits', 0, 1))[0]
    assert 'any' == code
    await bridge_service.REDIS.flushall()


async def test_add_visits_to_wrong_entity_returns_422(mocker, test_async_client):
    mocker.patch('app.auth.get_current_identity', return_value={'username': 'admin'})
    params = {'entity': 'any', 'code': 'any'}

    response = await test_async_client.post('/v1/visits', json=params)
    assert response.status_code == 422


@pytest.mark.parametrize(
    'entity,url',
    [
        ('project', f'{ConfigClass.PROJECT_SERVICE}/v1/projects'),
        ('dataset', f'{ConfigClass.DATASET_SERVICE}datasets'),
    ],
)
async def test_add_visits_returns_400_when_entity_does_not_exist(entity, url, mocker, test_async_client, httpx_mock):
    mocker.patch('app.auth.get_current_identity', return_value={'username': 'admin'})
    httpx_mock.add_response(
        method='GET',
        url=f'{url}/any',
        status_code=404,
        json={},
    )
    params = {'entity': entity, 'code': 'any'}

    response = await test_async_client.post('/v1/visits', json=params)
    assert response.status_code == 400
    assert response.json() == {'code': 400, 'error_msg': f'{entity} does not exist', 'result': ''}


async def test_add_visits_redis_error_returns_400(mocker, test_async_client, httpx_mock):
    mocker.patch('app.auth.get_current_identity', return_value={'username': 'admin'})
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.PROJECT_SERVICE}/v1/projects/any',
        json={'code': 'any'},
    )
    mocked_redis = mocker.patch.object(Redis, 'exists')
    mocked_redis.side_effect = RedisError()
    params = {'entity': 'project', 'code': 'any'}

    response = await test_async_client.post('/v1/visits', json=params)
    assert response.status_code == 400
    assert response.json() == {'code': 400, 'error_msg': 'add visits ERROR', 'result': ''}


@pytest.mark.parametrize('missing_field,params', [('last', {'entity': 'project'}), ('entity', {'last': 1})])
async def test_get_visits_returns_422_when_wrong_query_string(mocker, test_async_client, missing_field, params):
    mocker.patch('app.auth.get_current_identity', return_value={'username': 'admin'})
    response = await test_async_client.get('/v1/visits', query_string=params)
    assert response.json() == {
        'detail': [{'loc': ['query', missing_field], 'msg': 'field required', 'type': 'value_error.missing'}]
    }
    assert response.status_code == 422


async def test_get_visits_with_no_visits_returns_404(mocker, test_async_client):
    mocker.patch('app.auth.get_current_identity', return_value={'username': 'admin'})
    params = {'entity': 'project', 'last': 1}

    response = await test_async_client.get('/v1/visits', query_string=params)
    assert response.status_code == 200
    assert response.json() == {'code': 200, 'error_msg': '', 'num_of_pages': 1, 'page': 1, 'result': [], 'total': 1}


@pytest.mark.parametrize(
    'entity,url,service_response,api_response',
    [
        ('project', f'{ConfigClass.PROJECT_SERVICE}/v1/projects/', {'result': []}, {'result': []}),
        ('dataset', f'{ConfigClass.DATASET_SERVICE}datasets/', {'result': []}, {'result': []}),
        (
            'project',
            f'{ConfigClass.PROJECT_SERVICE}/v1/projects/',
            {'result': [{'code': 'code_1'}, {'code': 'code_2'}]},
            {'result': [{'code': 'code_2'}, {'code': 'code_1'}]},
        ),
        (
            'dataset',
            f'{ConfigClass.DATASET_SERVICE}datasets/',
            {'result': [{'code': 'code_1'}, {'code': 'code_2'}]},
            {'result': [{'code': 'code_2'}, {'code': 'code_1'}]},
        ),
    ],
)
async def test_get_visits_with_returns_200(
    mocker, test_async_client, httpx_mock, entity, url, service_response, api_response
):
    bridge_service = await get_bridge_service()
    username = 'admin'
    redis_cli = await Redis.from_url(ConfigClass.REDIS_URL, decode_responses=True)
    for i in range(0, 3):
        await redis_cli.lpush(f'{entity}:{username}:visits', f'code_{i}')

    mocker.patch('app.auth.get_current_identity', return_value={'username': username})
    httpx_mock.add_response(
        method='GET',
        url=f'{url}?code_any=code_2,code_1',
        status_code=200,
        json=service_response,
    )

    params = {'entity': entity, 'last': 2}
    response = await test_async_client.get('/v1/visits', query_string=params)
    assert response.json() == api_response
    assert response.status_code == 200
    await bridge_service.REDIS.flushall()
