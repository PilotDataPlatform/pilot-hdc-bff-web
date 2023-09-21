# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import requests
from common import ProjectClient
from common import has_permission
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_utils import cbv
from starlette.datastructures import MultiDict

from app.auth import jwt_required
from app.logger import logger
from config import ConfigClass
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode
from services.permissions_service.decorators import PermissionsCheck
from services.search.client import SearchServiceClient
from services.search.client import get_search_service_client

router = APIRouter(tags=['Project'])


@cbv.cbv(router)
class RestfulProject:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/project/{project_id}',
        summary='Get project by id',
        dependencies=[Depends(PermissionsCheck('project', '*', 'view'))],
    )
    async def get(self, project_id: str):
        my_res = APIResponse()
        project_client = ProjectClient(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
        project = await project_client.get(id=project_id)
        my_res.set_result(await project.json())
        return my_res.json_response()


@cbv.cbv(router)
class RestfulProjectByCode:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/project/code/{project_code}',
        summary='Get project by code',
        dependencies=[Depends(PermissionsCheck('project', '*', 'view'))],
    )
    async def get(self, project_code: str):
        my_res = APIResponse()
        project_client = ProjectClient(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
        project = await project_client.get(code=project_code)
        my_res.set_result(await project.json())
        return my_res.json_response()


@cbv.cbv(router)
class VirtualFolder:
    current_identity: dict = Depends(jwt_required)

    @router.put(
        '/project/{project_id}/collections',
        summary='Update project collections',
    )
    async def put(self, project_id: str, request: Request):
        url = ConfigClass.METADATA_SERVICE + 'collection/'
        payload = await request.json()
        payload['owner'] = self.current_identity['username']
        response = requests.put(url, json=payload, timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT)
        return JSONResponse(content=response.json(), status_code=response.status_code)


@cbv.cbv(router)
class ActivityLogs:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/project/activity-logs/{project_id}',
        summary='Fetch activity logs of a project from the search service',
        dependencies=[Depends(PermissionsCheck('project', '*', 'view'))],
    )
    async def get(
        self,
        project_id: str,
        request: Request,
        search_service_client: SearchServiceClient = Depends(get_search_service_client),
    ):
        """Fetch activity logs of a project."""
        _res = APIResponse()
        logger.info(f'Call API for fetching logs for project: {project_id}')

        try:
            params = MultiDict(request.query_params)
            project_client = ProjectClient(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
            project = await project_client.get(id=project_id)

            if not await has_permission(
                ConfigClass.AUTH_SERVICE, project.code, 'file_any', 'greenroom', 'view', self.current_identity
            ):
                params['user'] = self.current_identity['username']
            if not await has_permission(
                ConfigClass.AUTH_SERVICE, project.code, 'file_any', 'core', 'view', self.current_identity
            ):
                params['user'] = self.current_identity['username']

            params['container_code'] = project.code
            result = await search_service_client.get_item_activity_logs(params)
            logger.info('Successfully fetched data from search service')
            return result
        except Exception as e:
            logger.error(f'Failed to query item activity log from search service: {e}')
            _res.set_code(EAPIResponseCode.internal_error)
            _res.set_result(f'Failed to query item activity log from search service: {e}')
            return _res.json_response()
