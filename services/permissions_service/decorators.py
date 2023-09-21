# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from http import HTTPStatus
from typing import Optional

from common import ProjectClient
from common import has_permission
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request

from app.auth import get_current_identity
from app.components.exceptions import APIException
from app.logger import logger
from config import ConfigClass
from models.api_response import EAPIResponseCode
from services.dataset import get_dataset_by_code
from services.dataset import get_dataset_by_id
from services.permissions_service.utils import get_project_code_from_request
from services.project.client import get_project_service_client


async def find_project_code(
    project_code: Optional[str] = None,
    project_id: Optional[str] = None,
    project_service_client: ProjectClient = Depends(get_project_service_client),
) -> Optional[str]:
    """Find project code through a FastAPI dependency."""

    if project_code is not None and project_id is not None:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='project_code and project_id in one request are mutually exclusive',
        )

    if project_code is not None:
        return project_code

    if project_id is not None:
        project = await project_service_client.get(id=project_id)
        return project.code

    return None


class PermissionsCheck:
    def __init__(self, resource, zone, operation):
        self.resource = resource
        self.zone = zone
        self.operation = operation

    async def __call__(self, request: Request, project_code: Optional[str] = Depends(find_project_code)) -> bool:
        if project_code is None:
            project_code = await get_project_code_from_request(request)

        if not project_code:
            logger.error("Couldn't get project_code in permissions_check decorator")

        current_identity = await get_current_identity(request)
        if await has_permission(
            ConfigClass.AUTH_SERVICE, project_code, self.resource, self.zone, self.operation, current_identity
        ):
            return True

        logger.info(f'Permission denied for {project_code} - {self.resource} - {self.zone} - {self.operation}')
        raise APIException(error_msg='Permission denied', status_code=EAPIResponseCode.forbidden.value)


class DatasetPermission:
    async def __call__(self, request: Request):
        try:
            data = await request.json()
            dataset_code = request.path_params.get('dataset_code') or data.get('dataset_code')
            dataset_id = request.path_params.get('dataset_id')
            if not dataset_id:
                dataset_id = data.get('dataset_id') or data.get('dataset_geid') or data.get('dataset_id_or_code')
            if dataset_code:
                dataset = await get_dataset_by_code(dataset_code)
            else:
                dataset = await get_dataset_by_id(dataset_id)
            current_identity = await get_current_identity(request)
            if dataset['creator'] != current_identity['username']:
                raise APIException(error_msg='Permission denied', status_code=EAPIResponseCode.forbidden.value)
            return True
        except Exception:
            logger.exception('error while get dataset permission')
            return False
