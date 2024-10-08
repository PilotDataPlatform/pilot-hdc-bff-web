# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from common.project.project_client import ProjectObject
from fastapi import Depends

from app.auth import jwt_required
from app.components.exceptions import APIException
from app.components.user.models import CurrentUser
from models.api_response import EAPIResponseCode
from services.auth.client import AuthServiceClient
from services.auth.client import get_auth_service_client
from services.project.client import ProjectServiceClient
from services.project.client import get_project_service_client


def admin_role_required(current_identity: CurrentUser = Depends(jwt_required)) -> CurrentUser:
    """Raise permission denied exception if current role is not admin."""

    if current_identity['role'] == 'admin':
        return current_identity

    raise APIException(error_msg='Permission denied', status_code=EAPIResponseCode.forbidden.value)


async def get_project(
    project_code: str,
    current_identity: CurrentUser = Depends(jwt_required),
    auth_service_client: AuthServiceClient = Depends(get_auth_service_client),
    project_service_client: ProjectServiceClient = Depends(get_project_service_client),
) -> ProjectObject:
    """Get project and check if current user has access to it."""

    current_role = current_identity['role']
    if current_role != 'admin':
        current_username = current_identity['username']
        project_codes = await auth_service_client.get_project_codes_where_user_has_role(current_username)
        if project_code not in project_codes:
            raise APIException(error_msg='Permission denied', status_code=EAPIResponseCode.forbidden.value)

    project = await project_service_client.get(code=project_code)

    return project
