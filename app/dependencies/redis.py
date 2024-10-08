# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import asyncio

from fastapi import Depends
from redis.asyncio import Redis
from redis.exceptions import ConnectionError

from config import Settings
from config import get_settings


class GetRedis:
    """Class to create Redis connection instance."""

    def __init__(self) -> None:
        self.instance = None
        self.lock = asyncio.Lock()

    async def __call__(self, settings: Settings = Depends(get_settings)) -> Redis:
        """Return an instance of Redis class."""

        async with self.lock:
            if not self.instance:
                self.instance = Redis.from_url(
                    settings.REDIS_URL,
                    socket_keepalive=True,
                    retry_on_timeout=True,
                    retry_on_error=[ConnectionError],
                )
            return self.instance


get_redis = GetRedis()
