# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from fastapi import Depends
from httpx import AsyncClient
from httpx import Response

from api.api_notification.parameters import NotificationType
from api.api_project_files import get_zone_label
from app.logger import logger
from config import Settings
from config import get_settings


class NotificationServiceException(Exception):
    """Raised when any unexpected behaviour occurred while querying notification service."""


class NotificationServiceClient:
    """Client for notification service."""

    def __init__(self, endpoint: str, timeout: int) -> None:
        self.endpoint_v1 = f'{endpoint}/v1'
        self.endpoint_v2 = f'{endpoint}/v2'
        self.client = AsyncClient(timeout=timeout)

    async def _get(self, url: str, params: Mapping[str, Any]) -> Response:
        logger.info(f'Calling notification service {url} with query params: {params}')

        try:
            response = await self.client.get(url, params=params)
            assert response.is_success
        except Exception:
            message = f'Unable to query data from notification service with url "{url}" and params "{params}".'
            logger.exception(message)
            raise NotificationServiceException(message)

        return response

    async def get_all_notifications(self, params: Mapping[str, Any]) -> dict[str, Any]:
        """Query all notifications."""

        url = self.endpoint_v1 + '/all/notifications/'
        response = await self._get(url, params)

        return response.json()

    async def get_user_notifications(self, params: Mapping[str, Any]) -> dict[str, Any]:
        """Query user notifications."""

        url = self.endpoint_v1 + '/all/notifications/user'
        response = await self._get(url, params)

        return response.json()

    def replace_zone_labels(self, response: dict[str, Any]) -> dict[str, Any]:
        """Replace zone numbers with string values in notifications response."""

        for notification in response['result']:
            for key in ('source', 'destination'):
                try:
                    assert notification[key]
                    notification[key]['zone'] = get_zone_label(notification[key]['zone'])
                except (AssertionError, KeyError):
                    pass

        return response

    async def list_maintenance_announcements(self, params: Mapping[str, Any]) -> Response:
        """List maintenance announcements."""

        url = f'{self.endpoint_v2}/announcements/'
        response = await self.client.get(url, params=params)

        return response

    async def get_maintenance_announcement(self, announcement_id: UUID) -> dict[str, Any]:
        """Get maintenance announcement."""

        url = f'{self.endpoint_v2}/announcements/{announcement_id}'
        response = await self.client.get(url)

        return response.json()

    async def create_maintenance_announcement(self, json: dict[str, Any]) -> dict[str, Any]:
        """Create maintenance announcement."""

        url = f'{self.endpoint_v2}/announcements/'
        response = await self.client.post(url, json=json)

        return response.json()

    async def update_maintenance_announcement(self, announcement_id: UUID, json: dict[str, Any]) -> dict[str, Any]:
        """Update maintenance announcement."""

        url = f'{self.endpoint_v2}/announcements/{announcement_id}'
        response = await self.client.patch(url, json=json)

        return response.json()

    async def delete_maintenance_announcement(self, announcement_id: UUID) -> Response:
        """Delete maintenance announcement."""

        url = f'{self.endpoint_v2}/announcements/{announcement_id}'
        response = await self.client.delete(url)

        return response

    async def unsubscribe_from_maintenance_announcement(self, announcement_id: UUID, username: str) -> Response:
        """Unsubscribe from maintenance announcement."""

        url = f'{self.endpoint_v2}/announcements/{announcement_id}/unsubscribe'
        json = {'username': username}
        response = await self.client.post(url, json=json)

        return response

    async def list_project_notifications(self, project_code: str, params: Mapping[str, Any]) -> Response:
        """List project notifications."""

        url = f'{self.endpoint_v1}/all/notifications/'
        params['type'] = NotificationType.PROJECT.value
        params['project_code_any'] = project_code
        response = await self.client.get(url, params=params)

        return response

    async def create_project_notification(
        self, project_code: str, project_name: str, announcer_username: str, message: str
    ) -> Response:
        """Create project notification."""

        url = f'{self.endpoint_v1}/all/notifications/'
        json = {
            'type': NotificationType.PROJECT.value,
            'project_code': project_code,
            'project_name': project_name,
            'announcer_username': announcer_username,
            'message': message,
        }
        response = await self.client.post(url, json=json)

        return response


def get_notification_service_client(settings: Settings = Depends(get_settings)) -> NotificationServiceClient:
    """Get notification service client as a FastAPI dependency."""

    return NotificationServiceClient(settings.NOTIFY_SERVICE, settings.SERVICE_CLIENT_TIMEOUT)
