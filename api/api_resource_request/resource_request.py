# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import math
from datetime import datetime

import httpx
from common import ProjectClient
from common import has_permission
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_utils import cbv

from app.auth import jwt_required
from app.components.exceptions import APIException
from app.logger import logger
from config import ConfigClass
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode
from models.resource_request import CreateResourceRequest
from models.resource_request import UpdateResourceRequest
from services.notifier_services.email_service import SrvEmail
from services.permissions_service.decorators import PermissionsCheck

router = APIRouter(tags=['Resource Request'])


@cbv.cbv(router)
class ResourceRequest:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/resource-request/{request_id}/',
        summary='Get a single resource request',
        dependencies=[Depends(PermissionsCheck('resource_request', '*', 'manage'))],
    )
    async def get(self, request_id: str):
        """Get a single resource request."""
        api_response = APIResponse()
        logger.info('ResourceRequest get called')

        if self.current_identity['role'] != 'admin':
            api_response.set_error_msg('Permissions denied')
            api_response.set_code(EAPIResponseCode.forbidden)
            return api_response.json_response()

        try:
            async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                url = ConfigClass.PROJECT_SERVICE + f'/v1/resource-requests/{request_id}'
                response = await client.get(url)
        except Exception as e:
            logger.error(f'Error calling resource request API: {e}')
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_result(f'Error calling project service: {e}')
            return api_response.json_response()
        api_response.set_result(response.json())
        api_response.set_code(response.status_code)
        return api_response.json_response()

    @router.delete(
        '/resource-request/{request_id}/',
        summary='Delete a single resource request',
        dependencies=[Depends(PermissionsCheck('resource_request', '*', 'manage'))],
    )
    async def delete(self, request_id: str):
        api_response = APIResponse()
        logger.info('ResourceRequest get called')

        try:
            async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                url = ConfigClass.PROJECT_SERVICE + f'/v1/resource-requests/{request_id}'
                response = await client.delete(url)
        except Exception as e:
            logger.error(f'Error calling resource request API: {e}')
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_result(f'Error calling project service: {e}')
            return api_response.json_response()
        if response.status_code == 204:
            api_response.set_result('success')
            api_response.set_code(EAPIResponseCode.success.value)
        else:
            api_response.set_result(response.json())
            api_response.set_code(response.status_code)
        return api_response.json_response()

    @router.patch(
        '/resource-request/{request_id}/',
        summary='Update a single resource request',
        dependencies=[Depends(PermissionsCheck('resource_request', '*', 'manage'))],
    )
    async def patch(self, request_id: str, data: UpdateResourceRequest):
        api_response = APIResponse()

        async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
            url = ConfigClass.PROJECT_SERVICE + f'/v1/resource-requests/{request_id}'
            response = await client.get(url)
        resource_request = response.json()

        payload = {
            'container_code': resource_request['project']['code'],
            'username': resource_request['username'],
        }
        vm_connections = resource_request['vm_connections'] or {}
        for connection in data.connections:
            payload['connection_name'] = connection['name']
            payload['permissions'] = connection['permissions']
            payload['operation'] = connection['operation']

            async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                url = ConfigClass.WORKSPACE_SERVICE + 'guacamole/permission'
                response = await client.post(url, json=payload)
                if response.status_code != 200:
                    raise APIException(
                        error_msg='Error updating guacamole permissons' + str(response.json()),
                        status_code=response.status_code,
                    )
                if connection['operation'] == 'add':
                    vm_connections[connection['name']] = connection['permissions']
                else:
                    del vm_connections[connection['name']]
            resource_request['vm_connections'] = vm_connections
        try:
            payload = {'vm_connections': resource_request['vm_connections']}
            async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                url = ConfigClass.PROJECT_SERVICE + f'/v1/resource-requests/{request_id}'
                response = await client.patch(url, json=payload)
                if response.status_code != 200:
                    raise APIException(
                        error_msg='Error updating guacamole permissons' + str(response.json()),
                        status_code=response.status_code,
                    )
                resource_request = response.json()
        except Exception as e:
            logger.error(f'Error calling resource request API: {e}')
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_result(f'Error calling project service: {e}')
            return api_response.json_response()
        api_response.set_result(response.json())
        return api_response.json_response()


@cbv.cbv(router)
class ResourceRequestComplete:
    current_identity: dict = Depends(jwt_required)

    @router.put(
        '/resource-request/{request_id}/complete',
        summary='Update an existing resource request as complete',
    )
    async def put(self, request_id: str):
        """Update an existing resource request as complete."""
        api_response = APIResponse()
        logger.info('ResourceRequestComplete put called')

        try:
            async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                url = ConfigClass.PROJECT_SERVICE + f'/v1/resource-requests/{request_id}'
                response = await client.get(url)
            resource_request = response.json()
        except Exception as e:
            logger.error(f'Error calling resource request API: {e}')
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_result(f'Error calling project service: {e}')
            return api_response.json_response()

        project_client = ProjectClient(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
        project = await project_client.get(id=resource_request['project_id'])

        if not await has_permission(
            ConfigClass.AUTH_SERVICE, project.code, 'resource_request', '*', 'manage', self.current_identity
        ):
            api_response.set_code(EAPIResponseCode.forbidden)
            api_response.set_error_msg('Permission denied')
            return api_response.json_response()

        try:
            payload = {'completed_at': str(datetime.utcnow())}
            async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                url = ConfigClass.PROJECT_SERVICE + f'/v1/resource-requests/{request_id}'
                response = await client.patch(url, json=payload)
                resource_request = response.json()
        except Exception as e:
            logger.error(f'Error calling resource request API: {e}')
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_result(f'Error calling project service: {e}')
            return api_response.json_response()

        async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
            user_id = resource_request['user_id']
            data = {
                'user_id': user_id,
                'exact': True,
            }
            user_response = await client.get(ConfigClass.AUTH_SERVICE + 'admin/user', params=data)
            if user_response.status_code != 200:
                raise APIException(
                    error_msg=f'Error getting user {user_id} from auth service: ' + str(user_response.json()),
                    status_code=user_response.status_code,
                )
            user = user_response.json()['result']

        requested_for = resource_request['requested_for']
        template_kwargs = {
            'current_user': self.current_identity['username'],
            'request_for': requested_for,
            'project_name': project.name,
            'project_code': project.code,
            'admin_email': ConfigClass.EMAIL_SUPPORT,
        }
        try:
            user_email = user['email']
            email_sender = SrvEmail()
            await email_sender.async_send(
                f'Access granted to {requested_for}',
                [user_email],
                msg_type='html',
                template='resource_request/approved.html',
                template_kwargs=template_kwargs,
            )
            logger.info(f'Email sent to {user_email}')
        except Exception as e:
            logger.error(f'Error sending email: {e}')
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_result(f'Error sending email: {e}')
            return api_response.json_response()
        api_response.set_result(response.json())
        return api_response.json_response()


@cbv.cbv(router)
class ResourceRequestsQuery:
    current_identity: dict = Depends(jwt_required)

    @router.post(
        '/resource-requests/query',
        summary='List resource requests',
    )
    async def post(self, request: Request):
        """List resource requests."""
        logger.info('ResourceRequestsQuery post called')
        api_response = APIResponse()
        data = await request.json()

        page = int(data.get('page', 0))
        page = page
        page_size = int(data.get('page_size', 25))
        order_by = data.get('order_by', 'requested_at')
        order_type = data.get('order_type', 'asc')
        username = data.get('username', '')
        email = data.get('email', '')
        project_code = data.get('project_code')

        if username:
            username += '%'
        if email:
            email += '%'

        try:
            if not await has_permission(
                ConfigClass.AUTH_SERVICE, project_code, 'resource_request', '*', 'manage', self.current_identity
            ):
                if not await has_permission(
                    ConfigClass.AUTH_SERVICE, project_code, 'resource_request', '*', 'create', self.current_identity
                ):
                    api_response.set_code(EAPIResponseCode.forbidden)
                    api_response.set_error_msg('Permission denied')
                    return api_response.json_response()
                username = self.current_identity['username']

            payload = {
                'page': page,
                'page_size': page_size,
                'sort_by': order_by,
                'sort_order': order_type,
                'username': username,
                'email': email,
                'project_code': project_code,
            }
            async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                url = ConfigClass.PROJECT_SERVICE + '/v1/resource-requests/'
                response = await client.get(url, params=payload)
        except Exception as e:
            logger.error(f'Error calling project service: {e}')
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_result(f'Error calling project service: {e}')
            return api_response.json_response()

        if response.status_code != 200:
            return JSONResponse(content=response.json(), status_code=response.status_code)

        results = response.json()['result']
        for result in results:
            if result['completed_at']:
                result['is_completed'] = True
            else:
                result['is_completed'] = False

        total = response.json()['total']
        api_response.set_page(page)
        api_response.set_num_of_pages(math.ceil(total / page_size))
        api_response.set_total(total)
        api_response.set_result(results)
        return api_response.json_response()


@cbv.cbv(router)
class ResourceRequests:
    current_identity: dict = Depends(jwt_required)

    @router.post(
        '/resource-requests',
        summary='Create a new resource request, send email notification',
        dependencies=[Depends(PermissionsCheck('resource_request', '*', 'create'))],
    )
    async def post(self, data: CreateResourceRequest):

        """Create a new resource request, send email notification."""
        logger.info('ResourceRequests post called')
        api_response = APIResponse()

        project_client = ProjectClient(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
        project = await project_client.get(id=data.project_id)

        user_role = None
        for role in self.current_identity['realm_roles']:
            if role.split('-')[0] == project.code:
                user_role = role.split('-')[-1]
                break

        if not user_role:
            raise APIException(error_msg="Couldn't get user role", status_code=EAPIResponseCode.forbidden.value)

        payload = {
            'project_id': data.project_id,
            'user_id': self.current_identity['user_id'],
            'email': self.current_identity['email'],
            'username': self.current_identity['username'],
            'requested_for': data.request_for,
            'message': data.message,
        }
        async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
            url = ConfigClass.PROJECT_SERVICE + '/v1/resource-requests/'
            response = await client.post(url, json=payload)
            if response.status_code != 200:
                raise APIException(error_msg=response.json(), status_code=response.status_code)
        resource_request = response.json()

        username = self.current_identity['username']
        await send_email(resource_request, project, user_role, username)
        api_response.set_result(resource_request)
        return api_response.json_response()


async def send_email(resource_request, project, user_role, username):
    template_kwargs = {
        'username': username,
        'request_for': resource_request['requested_for'],
        'project_name': project.name,
        'project_code': project.code,
        'admin_email': ConfigClass.EMAIL_SUPPORT,
        'portal_url': ConfigClass.SITE_DOMAIN,
        'user_role': user_role.title(),
    }
    try:
        query = {'username': ConfigClass.RESOURCE_REQUEST_ADMIN}
        async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
            response = await client.get(ConfigClass.AUTH_SERVICE + 'admin/user', params=query)
        admin_email = response.json()['result']['email']
    except Exception as e:
        error_msg = f'Error getting admin email: {e}'
        logger.error(error_msg)
        raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.internal_error.value)

    try:
        email_sender = SrvEmail()
        await email_sender.async_send(
            'Resource Request from ' + template_kwargs['username'],
            [admin_email],
            msg_type='html',
            template='resource_request/request.html',
            template_kwargs=template_kwargs,
        )
        logger.info(f'Email sent to {admin_email}')
    except Exception as e:
        error_msg = f'Error sending email: {e}'
        logger.error(error_msg)
        raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.internal_error.value)
