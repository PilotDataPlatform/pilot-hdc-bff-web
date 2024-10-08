# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import pytest
from redis.asyncio import Redis

from app.dependencies.redis import GetRedis


@pytest.fixture
def get_redis() -> GetRedis:
    return GetRedis()


class TestGetRedis:
    async def test_instance_has_uninitialized_instance_attribute_after_creation(self, get_redis):
        assert get_redis.instance is None

    async def test_call_returns_an_instance_of_redis(self, get_redis, settings):
        redis = await get_redis(settings=settings)
        assert redis is get_redis.instance
        assert isinstance(redis, Redis)
