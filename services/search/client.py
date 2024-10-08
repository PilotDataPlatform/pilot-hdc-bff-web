# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Any
from typing import Dict
from typing import Mapping

from fastapi import Depends
from httpx import AsyncClient
from httpx import Response

from app.logger import logger
from config import Settings
from config import get_settings


class SearchServiceException(Exception):
    """Raised when any unexpected behaviour occurred while querying search service."""


class SearchServiceClient:
    """Client for search service."""

    def __init__(self, endpoint: str, timeout: int) -> None:
        self.endpoint_v1 = f'{endpoint}/v1'
        self.client = AsyncClient(timeout=timeout)

    async def _get(self, url: str, params: Mapping[str, Any]) -> Response:
        logger.info(f'Calling search service {url} with query params: {params}')

        try:
            response = await self.client.get(url, params=params)
            assert response.is_success
        except Exception:
            message = f'Unable to query data from search service with url "{url}" and params "{params}".'
            logger.exception(message)
            raise SearchServiceException(message)

        return response

    async def get_metadata_items(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        """Query metadata items."""

        url = self.endpoint_v1 + '/metadata-items/'
        response = await self._get(url, params)

        return response.json()

    async def get_dataset_activity_logs(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        """Query dataset activity logs."""

        url = self.endpoint_v1 + '/dataset-activity-logs/'
        response = await self._get(url, params)

        return response.json()

    async def get_item_activity_logs(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        """Query item activity logs."""

        url = self.endpoint_v1 + '/item-activity-logs/'
        response = await self._get(url, params)

        return response.json()

    async def get_project_size(self, project_code: str, params: Mapping[str, Any]) -> Dict[str, Any]:
        """Get storage usage for a project."""

        url = self.endpoint_v1 + f'/project-files/{project_code}/size'
        response = await self._get(url, params)
        return response.json()

    async def get_project_statistics(self, project_code: str, params: Mapping[str, Any]) -> Dict[str, Any]:
        """Get files and transfer activity statistics for a project."""

        url = self.endpoint_v1 + f'/project-files/{project_code}/statistics'
        response = await self._get(url, params)

        return response.json()

    async def get_project_activity(self, project_code: str, params: Mapping[str, Any]) -> Dict[str, Any]:
        """Get file activity statistic for a project."""

        url = self.endpoint_v1 + f'/project-files/{project_code}/activity'
        response = await self._get(url, params)

        return response.json()


def get_search_service_client(settings: Settings = Depends(get_settings)) -> SearchServiceClient:
    """Get search service client as a FastAPI dependency."""

    return SearchServiceClient(settings.SEARCH_SERVICE, settings.SERVICE_CLIENT_TIMEOUT)
