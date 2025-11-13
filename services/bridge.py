# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import itertools
from typing import Annotated
from typing import Any

from common.project.project_exceptions import ProjectNotFoundException
from fastapi import Depends
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.components.exceptions import APIException
from app.logger import logger
from config import ConfigClass
from services.dataset.client import DatasetServiceClient
from services.dataset.client import get_dataset_service_client
from services.project.client import ProjectServiceClient
from services.project.client import get_project_service_client


class BridgeService:

    REDIS = None
    BASE_VISIT_KEY = '{}:{}:visits'
    VISITS_LIMIT = 10

    def __init__(
        self, *, project_service_client: ProjectServiceClient, dataset_service_client: DatasetServiceClient
    ) -> None:
        self.project_service_client = project_service_client
        self.dataset_service_client = dataset_service_client

    async def _get_key(self, entity: str, username: str) -> bool:
        key = self.BASE_VISIT_KEY.format(entity, username)
        exists = await self.REDIS.exists(key)
        return key, exists

    async def _is_entity_exists(self, entity: str, code: str) -> bool:
        if entity == 'project':
            await self.project_service_client.get(code=code)
        else:
            await self.dataset_service_client.get_dataset_by_code(code)
        return True

    async def connect_redis(self) -> Redis:
        if not self.REDIS:
            logger.info('connection to redis')
            self.REDIS = await Redis.from_url(ConfigClass.REDIS_URL, decode_responses=True)
        return self.REDIS

    async def add_visit(self, entity: str, code: str, username: str) -> bool:
        try:
            await self._is_entity_exists(entity, code)
            key, key_exists = await self._get_key(entity, username)
            logger.info(f'key: {key}')
            if not key_exists:
                limit = self.VISITS_LIMIT - 1
                logger.info(f'setting trim to new key {limit}')
                await self.REDIS.ltrim(key, 0, limit)
            await self.REDIS.lrem(key, 0, code)
            await self.REDIS.lpush(key, code)
            return True
        except RedisError:
            raise APIException(400, 'add visits ERROR')
        except ProjectNotFoundException:
            raise APIException(400, f'{entity} does not exist')
        except APIException:
            raise APIException(400, f'{entity} does not exist')

    async def get_visits(self, entity: str, username: str, last: int) -> list:
        try:
            key, key_exists = await self._get_key(entity, username)
            logger.info(f'key: {key}')
            if not key_exists:
                return []
            logger.info(f'redis getting last {last} visits')
            return await self.REDIS.lrange(key, 0, last - 1)
        except RedisError:
            logger.exception('add visits ERROR')
            return []

    async def sort_result_by_visit_codes_order(
        self, codes: list[str], entity_result: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        result = []
        if entity_result:
            for codes_entities in itertools.product(codes, entity_result):
                if codes_entities[0] == codes_entities[1]['code']:
                    result.append(codes_entities[1])
            return result
        return entity_result


async def get_bridge_service(
    project_service_client: Annotated[ProjectServiceClient, Depends(get_project_service_client)],
    dataset_service_client: Annotated[DatasetServiceClient, Depends(get_dataset_service_client)],
) -> BridgeService:
    bridge_service = BridgeService(
        project_service_client=project_service_client, dataset_service_client=dataset_service_client
    )
    await bridge_service.connect_redis()
    return bridge_service


__all__ = 'get_bridge_service'
