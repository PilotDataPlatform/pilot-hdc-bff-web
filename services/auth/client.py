# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from json.decoder import JSONDecodeError
from typing import Any
from typing import List
from typing import Mapping

from fastapi import Depends
from httpx import AsyncClient
from httpx import Response

from app.components.exceptions import APIException
from app.logger import logger
from config import ConfigClass
from config import Settings
from config import get_settings
from models.api_response import EAPIResponseCode


class AuthServiceException(Exception):
    """Raised when any unexpected behaviour occurred while querying auth service."""


class AuthServiceClient:
    """Client for auth service."""

    def __init__(self, endpoint: str, timeout: int) -> None:
        self.endpoint_v1 = f'{endpoint}/v1'
        self.client = AsyncClient(timeout=timeout)

    async def _get(self, url: str, params: Mapping[str, Any]) -> Response:
        logger.info(f'Calling auth service url "{url}" with query params: {params}')

        try:
            response = await self.client.get(url, params=params)
            assert response.is_success
        except Exception:
            message = f'Unable to query data from auth service with url "{url}" and params "{params}".'
            logger.exception(message)
            raise AuthServiceException(message)

        return response

    async def get_project_codes_where_user_has_role(self, username: str) -> List[str]:
        """Get list of project codes where the user has a role."""

        url = self.endpoint_v1 + '/admin/users/realm-roles'
        params = {'username': username}
        response = await self._get(url, params)

        data = response.json()
        project_codes = {role['name'].split('-', 1).pop(0) for role in data['result']}

        return sorted(project_codes)

    async def get_project_roles(self, project_code: str) -> list[str]:
        try:
            payload = {'project_code': project_code}
            async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                response = await client.get(self.endpoint_v1 + '/permissions/metadata', params=payload)
            response.raise_for_status()
            project_roles = list(response.json()['result'][0]['permissions'].keys())
        except JSONDecodeError as e:
            message = f'Failed to get permissions metadata: {e}'
            logger.exception(message)
            raise APIException(error_msg=message, status_code=EAPIResponseCode.internal_error.value)
        except KeyError as e:
            message = f'Failed to get permissions metadata: {e}'
            logger.exception(message)
            raise APIException(error_msg=message, status_code=EAPIResponseCode.internal_error.value)
        return project_roles


def get_auth_service_client(settings: Settings = Depends(get_settings)) -> AuthServiceClient:
    """Get auth service client as a FastAPI dependency."""

    return AuthServiceClient(settings.AUTH_SERVICE.replace('/v1/', ''), settings.SERVICE_CLIENT_TIMEOUT)
