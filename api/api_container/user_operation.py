# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import math
from datetime import datetime

import httpx
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_utils import cbv
from httpx import AsyncClient

from app.auth import jwt_required
from app.components.user.models import CurrentUser
from app.logger import logger
from config import ConfigClass
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode
from services.auth.client import AuthServiceClient
from services.auth.client import get_auth_service_client
from services.permissions_service.decorators import PermissionsCheck
from services.project.client import ProjectServiceClient
from services.project.client import get_project_service_client

router = APIRouter(tags=['User Operations'])


@cbv.cbv(router)
class Users:
    current_identity: CurrentUser = Depends(jwt_required)

    @router.get(
        '/users/platform',
        summary='List all users in platform',
    )
    async def get(self, request: Request):
        """This method allow user to fetch all registered users in the platform."""
        logger.info('Call API for to admin fetching all users in the platform')
        api_response = APIResponse()
        if self.current_identity['role'] != 'admin':
            api_response.set_error_msg('Permission Denied')
            api_response.set_code(EAPIResponseCode.forbidden)
            return api_response.json_response()
        try:
            data = {
                'username': request.query_params.get('name', None),
                'email': request.query_params.get('email', None),
                'order_by': request.query_params.get('order_by', None),
                'order_type': request.query_params.get('order_type', None),
                'page': request.query_params.get('page', 0),
                'page_size': request.query_params.get('page_size', 25),
                'status': request.query_params.get('status', None),
                'role': request.query_params.get('role', None),
            }
            data = {k: v for k, v in data.items() if v}
            async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                response = await client.get(ConfigClass.AUTH_SERVICE + 'users', params=data)
        except Exception as e:
            api_response.set_error_msg(f'Error get users from auth service: {e}')
            api_response.set_code(EAPIResponseCode.internal_error)
            return api_response.json_response()
        return JSONResponse(content=response.json(), status_code=response.status_code)


@cbv.cbv(router)
class ContainerAdmins:
    current_identity: CurrentUser = Depends(jwt_required)
    project_service_client: ProjectServiceClient = Depends(get_project_service_client)

    @router.get(
        '/containers/{project_id}/admins',
        summary='List all admins in a project',
        dependencies=[Depends(PermissionsCheck('project', '*', 'view'))],
    )
    async def get(self, project_id: str):
        """This method allow user to fetch all admins under a specific project with permissions."""
        project = await self.project_service_client.get(project_id)

        payload = {
            'role_names': [f'{project.code}-admin'],
            'status': 'active',
        }
        async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
            response = await client.post(ConfigClass.AUTH_SERVICE + 'admin/roles/users', json=payload)
        return JSONResponse(content=response.json(), status_code=response.status_code)


@cbv.cbv(router)
class ContainerUsers:
    current_identity: CurrentUser = Depends(jwt_required)
    auth_client: AuthServiceClient = Depends(get_auth_service_client)
    project_service_client: ProjectServiceClient = Depends(get_project_service_client)

    @router.get(
        '/containers/{project_id}/users',
        summary='List all users in a project',
        dependencies=[Depends(PermissionsCheck('users', '*', 'view'))],
    )
    async def get(self, project_id: str, request: Request):
        """This method allow user to fetch all users under a specific dataset with permissions."""
        data = request.query_params
        logger.info(f'Calling API for fetching all users under dataset {project_id}')
        project = await self.project_service_client.get(id=project_id)

        project_roles = await self.auth_client.get_project_roles(project.code)

        payload = {
            'role_names': [f'{project.code}-{i}' for i in project_roles],
            'status': 'active',
            'username': data.get('username'),
            'email': data.get('email'),
            'page': data.get('page', 0),
            'page_size': data.get('page_size', 25),
            'order_by': data.get('order_by', 'time_created'),
            'order_type': data.get('order_type', 'desc'),
        }
        async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
            response = await client.post(ConfigClass.AUTH_SERVICE + 'admin/roles/users', json=payload)
        return JSONResponse(content=response.json(), status_code=response.status_code)


@cbv.cbv(router)
class ContainerUsersStats:
    current_identity: CurrentUser = Depends(jwt_required)
    project_service_client: ProjectServiceClient = Depends(get_project_service_client)

    @router.get(
        '/containers/{project_id}/roles/users/stats',
        summary='List number of users per realm role for a project',
        dependencies=[Depends(PermissionsCheck('users', '*', 'view'))],
    )
    async def get(self, project_id: str):
        """Allow user to fetch number of users under admin, collaborator, and contributor roles for a project."""
        api_response = APIResponse()
        try:
            logger.info(f'Calling API for fetching user realm role stats under project_id: {project_id}')
            project = await self.project_service_client.get(id=project_id)
            project_code = project.code
            logger.info(f'Fetched project code from project service: {project_code}')

            async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                response = await client.get(
                    ConfigClass.AUTH_SERVICE + 'admin/roles/users/stats', params={'project_code': project_code}
                )
                if response.status_code != 200:
                    raise Exception('Fetching stats from auth service failed')

            logger.info(f'Fetched user realm role stats from auth service for project: {project_code}')
            role_response = response.json()
            api_response.set_result(role_response['result'])
        except Exception as e:
            logger.exception(f'Failed to retrieve user realm role stats for project_id {project_id}: {e}')
            api_response.set_error_msg(f'Failed to retrieve user realm role stats for project_id {project_id}: {e}')
            api_response.set_code(EAPIResponseCode.internal_error)
        return api_response.json_response()


@cbv.cbv(router)
class UserContainerQuery:
    current_identity: CurrentUser = Depends(jwt_required)
    project_service_client: ProjectServiceClient = Depends(get_project_service_client)

    @router.post(
        '/users/{username}/containers',
        summary="Query user's containers",
    )
    async def post(self, username: str, request: Request):  # noqa: C901
        """This method allow user to get the user's permission towards all containers (except default)."""
        logger.info(f'Call API for fetching user {username} role towards all projects')
        data = await request.json()

        name = None
        if data.get('name'):
            name = '%' + data.get('name') + '%'
        code = None
        if data.get('code'):
            code = '%' + data.get('code') + '%'

        description = None
        if data.get('description'):
            description = '%' + data.get('description') + '%'

        payload = {
            'page': data.get('page', 0),
            'page_size': data.get('page_size', 25),
            'order_by': data.get('order_by', None),
            'order_type': data.get('order_type', None),
            'name': name,
            'code': code,
            'tags_all': data.get('tags'),
            'description': description,
        }

        query = {
            'username': username,
            'exact': True,
        }
        async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
            response = await client.get(ConfigClass.AUTH_SERVICE + 'admin/users/realm-roles', params=query)
        if response.status_code != 200:
            raise Exception(f'Error getting realm roles for {username} from auth service: ' + str(response.json()))
        realm_roles = {}
        is_platform_admin = False
        for role in response.json()['result']:
            try:
                if role['name'] == 'platform-admin':
                    is_platform_admin = True
                realm_roles[role['name'].split('-')[0]] = role['name'].split('-')[1]
            except Exception:
                continue

        if data.get('is_all'):
            payload['page_size'] = 999

        if 'create_time_start' in data and 'create_time_end' in data:
            start_time = datetime.utcfromtimestamp(int(data['create_time_start']))
            end_time = datetime.utcfromtimestamp(int(data['create_time_end']))
            payload['created_at_start'] = start_time.strftime('%Y-%m-%dT%H:%M:%S')
            payload['created_at_end'] = end_time.strftime('%Y-%m-%dT%H:%M:%S')

        if not is_platform_admin:
            roles = realm_roles
            project_codes = ','.join({i.split('-')[0] for i in roles})
            payload['code_any'] = project_codes
            if not project_codes:
                results = {
                    'results': [],
                    'role': 'member',
                    'total': 0,
                    'page': 0,
                    'num_of_pages': 1,
                }
                return results

        project_result = await self.project_service_client.search(**payload)
        projects = [await i.json() for i in project_result['result']]

        if not is_platform_admin:
            for project in projects:
                project['permission'] = realm_roles.get(project['code'])
        else:
            for project in projects:
                project['permission'] = 'admin'
        results = {
            'results': projects,
            'role': 'admin' if is_platform_admin else 'member',
            'total': project_result['total'],
            'page': project_result['page'],
            'num_of_pages': int(math.ceil(project_result['total'] / payload['page_size'])),
        }
        return results
