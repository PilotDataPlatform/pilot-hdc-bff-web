# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import json

import pytest
from common import ProjectClient
from common.project.project_client import CACHE_PREFIX
from fakeredis.aioredis import FakeRedis
from redis.asyncio import Redis


class ProjectClientMock(ProjectClient):
    def __init__(self, redis: Redis) -> None:
        super().__init__('', '', True, True)

        self.redis = redis
        self.prefix = CACHE_PREFIX

    async def connect_redis(self) -> None:
        pass

    async def create_project(self, id_: str, code: str) -> None:
        key = f'{self.prefix}{id_}'
        data = {'code': code}
        await self.redis.set(key, json.dumps(data))


@pytest.fixture
def project_client() -> ProjectClientMock:
    yield ProjectClientMock(redis=FakeRedis())
