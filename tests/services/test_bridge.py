# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from unittest.mock import AsyncMock

import pytest

from config import ConfigClass
from services.bridge import BridgeService
from services.bridge import get_bridge_service

pytestmark = pytest.mark.asyncio

ENTITY = 'entity'
CODE = 'code'
USERNAME = 'username'
KEY = f'{ENTITY}:{USERNAME}:visits'


@pytest.fixture
def mocked_redis(mocker):
    redis = mocker.patch.object(BridgeService, 'REDIS', side_effect=AsyncMock())
    redis.ltrim.side_effect = AsyncMock()
    redis.lpush.side_effect = AsyncMock()
    redis.lrange.side_effect = AsyncMock()
    redis.lrem.side_effect = AsyncMock()
    return redis


async def test_bridge_service_add_visit_calls_ltrim_lpush_when_key_doest_exist(mocked_redis, httpx_mock):
    mocked_redis.exists.side_effect = AsyncMock(return_value=False)
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.DATASET_SERVICE}datasets/{CODE}',
        status_code=200,
        json={'code': 'any'},
    )
    bridge_service = await get_bridge_service()
    await bridge_service.add_visit(ENTITY, CODE, USERNAME)

    mocked_redis.ltrim.assert_called_with(KEY, 0, bridge_service.VISITS_LIMIT - 1)
    mocked_redis.lrem.assert_called_with(KEY, 0, CODE)
    mocked_redis.lpush.assert_called_with(KEY, CODE)


async def test_bridge_service_add_visit_calls_lpush_when_key_exist(mocked_redis, httpx_mock):
    mocked_redis.exists.side_effect = AsyncMock(return_value=True)
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.DATASET_SERVICE}datasets/{CODE}',
        status_code=200,
        json={'code': 'any'},
    )
    bridge_service = await get_bridge_service()
    await bridge_service.add_visit(ENTITY, CODE, USERNAME)

    mocked_redis.ltrim.call_count = 0
    mocked_redis.lrem.assert_called_with(KEY, 0, CODE)
    mocked_redis.lpush.assert_called_with(KEY, CODE)


async def test_bridge_service_get_visits_calls_lrange(mocked_redis):
    mocked_redis.exists.side_effect = AsyncMock(return_value=True)
    last = 2

    bridge_service = await get_bridge_service()
    await bridge_service.get_visits(ENTITY, USERNAME, last)

    mocked_redis.lrange.assert_called_with(KEY, 0, last - 1)
