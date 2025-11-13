# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from collections.abc import Mapping
from enum import Enum
from typing import Any

from fastapi import Depends
from httpx import AsyncClient
from httpx import Response

from app.components.exceptions import ServiceException
from app.logger import logger
from config import Settings
from config import get_settings


class KGRole(str, Enum):
    """Mapping of KG roles to Project roles."""

    administrator = 'admin'
    editor = 'collaborator'
    viewer = 'contributor'


class KGServiceException(ServiceException):
    """Raised when any unexpected behaviour occurred while querying knowledge graph service."""

    def __init__(self, status: int, details: str):
        self.remote_status = status
        self.error_message = details

    @property
    def status(self) -> int:
        return self.remote_status

    @property
    def code(self) -> str:
        return 'kg_service_exception'

    @property
    def details(self) -> str:
        return self.error_message


class KGServiceClient:
    """Client for notification service."""

    def __init__(self, endpoint: str) -> None:
        self.endpoint = endpoint + '/v1'
        self.client = AsyncClient(timeout=1000)

    async def _get(self, url: str, params: Mapping[str, Any], headers: dict[str, Any] | None = None) -> Response:
        logger.info(f'Calling kg integration service {url} with query params: {params}')

        try:
            response = await self.client.get(url, params=params, headers=headers)
            assert response.is_success
        except AssertionError:
            message = f'Unable to query data from kg integration service with url "{url}" and params "{params}".'
            logger.exception(message)
            raise KGServiceException(status=response.status_code, details=response.text)

        return response

    async def _post(
        self, url: str, params: Mapping[str, Any], json: dict[str, Any], headers: dict[str, Any] | None = None
    ) -> Response:
        logger.info(f'Calling kg integration service {url} with query params: {params} and body: {json}')

        try:
            response = await self.client.post(url, params=params, json=json, headers=headers)
            assert response.is_success
        except AssertionError:
            message = f'Unable to send data to kg integration service with url "{url}" and params "{params}".'
            logger.exception(message)
            raise KGServiceException(status=response.status_code, details=response.text)

        return response

    async def _put(
        self, url: str, params: Mapping[str, Any], json: dict[str, Any], headers: dict[str, Any] | None = None
    ) -> Response:
        logger.info(f'Calling kg integration service {url} with query params: {params} and body: {json}')

        try:
            response = await self.client.put(url, params=params, json=json, headers=headers)
            assert response.is_success
        except AssertionError:
            message = f'Unable to send data to kg integration service with url "{url}" and params "{params}".'
            logger.exception(message)
            raise KGServiceException(status=response.status_code, details=response.text)

        return response

    async def list_available_spaces(self, **kwargs) -> Response:
        """List available spaces."""

        url = f'{self.endpoint}/spaces/'
        response = await self._get(url, **kwargs)

        return response

    async def check_existing_spaces(self, json: dict[str, Any], **kwargs) -> Response:
        """List available spaces."""

        url = f'{self.endpoint}/spaces/'
        response = await self._post(url, json=json, **kwargs)

        return response

    async def get_space_by_id(self, space: str, **kwargs) -> Response:
        """Get information about one space."""

        url = f'{self.endpoint}/spaces/{space}'
        response = await self._get(url, **kwargs)

        return response

    async def create_new_space(self, **kwargs) -> Response:
        """Create a new space with given name."""

        url = f'{self.endpoint}/spaces/create'
        response = await self._post(url, json={}, **kwargs)

        return response

    async def create_new_space_for_project(self, project_code: str, **kwargs) -> Response:
        """Create a new space with given name."""

        url = f'{self.endpoint}/spaces/create/project/{project_code}'
        response = await self._post(url, json={}, **kwargs)

        return response

    async def create_new_space_for_dataset(self, dataset_code: str, **kwargs) -> Response:
        """Create a new space with given name."""

        url = f'{self.endpoint}/spaces/create/dataset/{dataset_code}'
        response = await self._post(url, json={}, **kwargs)

        return response

    async def list_metadata(self, **kwargs) -> Response:
        """List all available metadata for given parameters."""

        url = f'{self.endpoint}/metadata/'
        response = await self._get(url, **kwargs)

        return response

    async def check_existing_metadata(self, json: dict[str, Any], **kwargs) -> Response:
        """List all available metadata for given parameters."""

        url = f'{self.endpoint}/metadata/'
        response = await self._post(url, json=json, **kwargs)

        return response

    async def get_metadata_by_id(self, metadata_id: str, **kwargs) -> Response:
        """Get metadata by specific id."""

        url = f'{self.endpoint}/metadata/{metadata_id}'
        response = await self._get(url, **kwargs)

        return response

    async def upload_metadata(self, json: dict[str, Any], **kwargs) -> Response:
        """Upload metadata to KG."""

        url = f'{self.endpoint}/metadata/upload'
        response = await self._post(url, json=json, **kwargs)

        return response

    async def upload_metadata_from_kg(self, kg_instance_id: str, dataset_id: str, **kwargs) -> Response:
        """Upload metadata to KG."""

        url = f'{self.endpoint}/metadata/upload/{kg_instance_id}/{dataset_id}'
        response = await self._get(url, **kwargs)

        return response

    async def refresh_metadata_from_kg(self, metadata_id: str, **kwargs) -> Response:
        """Refresh metadata from KG."""

        url = f'{self.endpoint}/metadata/refresh/{metadata_id}'
        response = await self._get(url, **kwargs)

        return response

    async def bulk_refresh_metadata_from_kg(self, dataset_id: str, **kwargs) -> Response:
        """Bulk refresh metadata from KG."""

        url = f'{self.endpoint}/metadata/refresh/dataset/{dataset_id}'
        response = await self._get(url, **kwargs)

        return response

    async def update_metadata(self, metadata_id: str, json: dict[str, Any], **kwargs) -> Response:
        """Update metadata on KG."""

        url = f'{self.endpoint}/metadata/update/{metadata_id}'
        response = await self._put(url, json=json, **kwargs)

        return response

    async def bulk_update_metadata(self, dataset_id: str, **kwargs) -> Response:
        """Bulk update metadata on KG."""

        url = f'{self.endpoint}/metadata/update/dataset/{dataset_id}'
        response = await self._put(url, json={}, **kwargs)

        return response

    async def delete_metadata(self, metadata_id: str, **kwargs) -> Response:
        """Delete metadata on KG."""

        url = f'{self.endpoint}/metadata/{metadata_id}'
        response = await self.client.delete(url, **kwargs)

        return response

    async def list_space_users(self, space: str, **kwargs) -> Response:
        """List all users for given role in KG space."""

        url = f'{self.endpoint}/users/{space}'
        response = await self._get(url, **kwargs)

        return response

    async def add_user_to_space(self, project_id: str, username: str, **kwargs) -> Response:
        """Add new user in given role to KG space."""

        url = f'{self.endpoint}/users/{project_id}/{username}'
        response = await self._post(url, json={}, **kwargs)

        return response

    async def remove_user_from_space(self, project_id: str, username: str, **kwargs) -> Response:
        """Remove a user with given role from KG space."""

        url = f'{self.endpoint}/users/{project_id}/{username}'
        response = await self.client.delete(url, **kwargs)

        return response

    async def update_user_role_for_space(self, project_id: str, username: str, **kwargs) -> Response:
        """Remove a user with given role from KG space."""

        url = f'{self.endpoint}/users/{project_id}/{username}'
        response = await self._put(url, json={}, **kwargs)

        return response


def get_kg_service_client(settings: Settings = Depends(get_settings)) -> KGServiceClient:
    """Get KG service client as a FastAPI dependency."""

    return KGServiceClient(settings.KG_SERVICE)
