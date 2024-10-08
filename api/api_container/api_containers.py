# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi_utils import cbv

from app.auth import jwt_required
from app.components.user.models import CurrentUser
from app.logger import logger
from models.api_response import APIResponse
from services.permissions_service.decorators import PermissionsCheck
from services.project.client import ProjectServiceClient
from services.project.client import get_project_service_client

router = APIRouter(tags=['Containers'])


@cbv.cbv(router)
class Containers:
    current_identity: CurrentUser = Depends(jwt_required)
    project_service_client: ProjectServiceClient = Depends(get_project_service_client)

    @router.get(
        '/containers/',
        summary='List and query all projects',
    )
    async def get(self, request: Request):
        """List and Query on all projects"."""
        logger.info('Calling Container get')
        api_response = APIResponse()

        name = None
        if request.query_params.get('name'):
            name = '%' + request.query_params.get('name') + '%'
        code = None
        if request.query_params.get('code'):
            code = '%' + request.query_params.get('code') + '%'

        description = None
        if request.query_params.get('description'):
            description = '%' + request.query_params.get('description') + '%'

        tags = request.query_params.get('tags')
        if tags:
            tags = tags.split(',')

        payload = {
            'page': request.query_params.get('page'),
            'page_size': request.query_params.get('page_size'),
            'order_by': request.query_params.get('order_by'),
            'order_type': request.query_params.get('order_type'),
            'name': name,
            'code': code,
            'tags_all': tags,
            'description': description,
        }
        if self.current_identity['role'] != 'admin':
            payload['is_discoverable'] = True

        if 'create_time_start' in request.query_params and 'create_time_end' in request.query_params:
            payload['created_at_start'] = request.query_params.get('create_time_start')
            payload['created_at_end'] = request.query_params.get('create_time_end')

        result = await self.project_service_client.search(**payload)
        api_response.set_result([await i.json() for i in result['result']])
        api_response.set_total(result['total'])
        api_response.set_num_of_pages(result['num_of_pages'])
        return api_response.json_response()


@cbv.cbv(router)
class Container:
    current_identity: CurrentUser = Depends(jwt_required)
    project_service_client: ProjectServiceClient = Depends(get_project_service_client)

    @router.put(
        '/containers/{project_id}',
        summary='Update a project',
        dependencies=[Depends(PermissionsCheck('project', '*', 'update'))],
    )
    async def put(self, project_id: str, request: Request):
        """Update a project."""
        logger.info('Calling Container put')
        api_response = APIResponse()
        update_data = await request.json()
        project = await self.project_service_client.get(id=project_id)

        if 'icon' in update_data:
            logo = update_data['icon']
            await project.upload_logo(logo)
            del update_data['icon']

        result = await project.update(**update_data)
        api_response.set_result(await result.json())
        return api_response.json_response()
