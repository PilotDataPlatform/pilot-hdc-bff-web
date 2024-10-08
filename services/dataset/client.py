# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Any
from typing import Mapping
from uuid import UUID

from fastapi import Depends
from httpx import AsyncClient
from httpx import Response

from config import Settings
from config import get_settings
from services.dataset import get_dataset_by_code
from services.dataset import get_dataset_by_id


class DatasetServiceClient:
    """Client for dataset service."""

    def __init__(self, endpoint: str, timeout: int) -> None:
        self.endpoint_v1 = f'{endpoint}/v1'
        self.client = AsyncClient(timeout=timeout)

    async def get_dataset_by_id(self, dataset_id: UUID) -> dict[str, Any]:
        """Get dataset by id."""

        return await get_dataset_by_id(dataset_id)

    async def get_dataset_by_code(self, dataset_code: str) -> dict[str, Any]:
        """Get dataset by code."""

        return await get_dataset_by_code(dataset_code)

    async def list_datasets(self, parameters: Mapping[str, str]) -> Response:
        """Get list of datasets."""

        return await self.client.get(f'{self.endpoint_v1}/datasets/', params=parameters)


def get_dataset_service_client(settings: Settings = Depends(get_settings)) -> DatasetServiceClient:
    """Get Dataset Service Client as a FastAPI dependency."""

    return DatasetServiceClient(settings.DATASET_SERVICE.replace('/v1/', ''), settings.SERVICE_CLIENT_TIMEOUT)
