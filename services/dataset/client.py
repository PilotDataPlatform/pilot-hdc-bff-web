# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from httpx import Response

from app.components.request.context import RequestContextDependency
from app.components.request.http_client import HTTPClient
from config import SettingsDependency
from services.dataset import get_dataset_by_code
from services.dataset import get_dataset_by_id


class DatasetServiceClient:
    """Client for dataset service."""

    def __init__(self, endpoint: str, client: HTTPClient) -> None:
        self.endpoint_v1 = f'{endpoint}/v1'
        self.client = client

    async def get_dataset_by_id(self, dataset_id: UUID) -> dict[str, Any]:
        """Get dataset by id."""

        return await get_dataset_by_id(dataset_id)

    async def get_dataset_by_code(self, dataset_code: str) -> dict[str, Any]:
        """Get dataset by code."""

        return await get_dataset_by_code(dataset_code)

    async def list_datasets(self, parameters: Mapping[str, str]) -> Response:
        """Get list of datasets."""

        return await self.client.get(f'{self.endpoint_v1}/datasets/', params=parameters)

    async def get_dataset_version(self, version_id: UUID) -> dict[str, Any]:
        """Get dataset version by id."""

        response = await self.client.get(f'{self.endpoint_v1}/dataset/versions/{version_id}')
        response.raise_for_status()

        return response.json()

    async def list_dataset_version_sharing_requests(self, parameters: Mapping[str, str]) -> Response:
        """Get list of dataset version sharing requests."""

        return await self.client.get(f'{self.endpoint_v1}/version-sharing-requests/', params=parameters)

    async def get_dataset_version_sharing_request(self, version_sharing_request_id: UUID) -> Response:
        """Get dataset version sharing request by id."""

        return await self.client.get(f'{self.endpoint_v1}/version-sharing-requests/{version_sharing_request_id}')

    async def create_dataset_version_sharing_request(
        self, dataset_version_id: UUID, project_code: str, shared_by_username: str
    ) -> Response:
        """Create dataset version sharing request."""

        return await self.client.post(
            f'{self.endpoint_v1}/version-sharing-requests/',
            json={
                'version_id': str(dataset_version_id),
                'project_code': project_code,
                'initiator_username': shared_by_username,
                'status': 'sent',
            },
        )

    async def process_dataset_version_sharing_request(
        self, version_sharing_request_id: UUID, processed_by_username: str, status: str
    ) -> Response:
        """Update dataset version sharing request status and processed by."""

        return await self.client.patch(
            f'{self.endpoint_v1}/version-sharing-requests/{version_sharing_request_id}',
            json={'status': status, 'receiver_username': processed_by_username},
        )

    async def start_version_sharing_request(
        self, version_sharing_request_id: UUID, job_id: str, session_id: str, authorization: str
    ) -> Response:
        """Start sharing of the dataset version specified in version sharing request."""

        return await self.client.post(
            f'{self.endpoint_v1}/version-sharing-requests/{version_sharing_request_id}/start',
            json={'job_id': job_id, 'session_id': session_id},
            headers={'Authorization': authorization},
        )


def get_dataset_service_client(
    request_context: RequestContextDependency, settings: SettingsDependency
) -> DatasetServiceClient:
    """Get Dataset Service Client as a FastAPI dependency."""

    return DatasetServiceClient(settings.DATASET_SERVICE.replace('/v1/', ''), request_context.client)
