# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import httpx
import requests
from common import get_project_role
from common import has_permission
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_utils import cbv
from httpx import AsyncClient

from app.auth import jwt_required
from app.components.exceptions import APIException
from app.components.user.models import CurrentUser
from app.logger import logger
from config import ConfigClass
from models.api_invitation import RegisterPOST
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode
from services.notifier_services.email_service import SrvEmail
from services.project.client import ProjectServiceClient
from services.project.client import get_project_service_client

router = APIRouter(tags=['Invitations'])


@cbv.cbv(router)
class InvitationsRestful:
    current_identity: CurrentUser = Depends(jwt_required)

    @router.post(
        '/invitations',
        summary='create invitation in platform',
    )
    async def post(self, request: Request):
        """This method allow to create invitation in platform."""
        post_json = await request.json()
        logger.info(f'Start Creating Invitation: {post_json}')
        if post_json.get('relationship'):
            project_code = post_json['relationship'].get('project_code')
            if not await has_permission(
                ConfigClass.AUTH_SERVICE, project_code, 'invitation', '*', 'manage', self.current_identity
            ):
                error_msg = 'Permission denied'
                raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.forbidden.value)
            post_json['inviter_project_role'] = await get_project_role(project_code, self.current_identity)

        if not post_json.get('relationship') and self.current_identity['role'] != 'admin':
            raise APIException(error_msg='Permission Denied', status_code=EAPIResponseCode.forbidden.value)

        try:
            post_json['invited_by'] = self.current_identity['username']
            async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                response = await client.post(ConfigClass.AUTH_SERVICE + 'invitations', json=post_json)
        except Exception as e:
            error_msg = f'Error calling Auth service for invite create: {e}'
            logger.error(error_msg)
            raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.internal_error.value)
        return JSONResponse(content=response.json(), status_code=response.status_code)


@cbv.cbv(router)
class CheckUserPlatformRole:
    current_identity: CurrentUser = Depends(jwt_required)

    @router.get(
        '/invitation/check/{email}',
        summary='Check if a user exists',
    )
    async def get(self, email: str, request: Request):
        my_res = APIResponse()

        project_code = request.query_params.get('project_code')

        if self.current_identity['role'] != 'admin' and not project_code:
            my_res.set_result('Permission denied')
            my_res.set_code(EAPIResponseCode.unauthorized)
            return my_res.json_response()

        params = {}
        if project_code:
            if not await has_permission(
                ConfigClass.AUTH_SERVICE, project_code, 'invitation', '*', 'manage', self.current_identity
            ):
                my_res.set_result('Permission denied')
                my_res.set_code(EAPIResponseCode.unauthorized)
                return my_res.json_response()
            params['project_code'] = project_code
        try:
            async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                response = await client.get(ConfigClass.AUTH_SERVICE + f'invitation/check/{email}', params=params)
        except Exception as e:
            error_msg = f'Error calling Auth service for invite check: {e}'
            logger.error(error_msg)
            raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.internal_error.value)
        return JSONResponse(content=response.json(), status_code=response.status_code)


@cbv.cbv(router)
class Register:
    @router.get(
        '/register/invitation/{invitation_code}',
        summary='Get invitation by invitation code',
    )
    async def get(self, invitation_code: str):
        payload = {'filters': {'invitation_code': invitation_code, 'status': 'sent'}}
        async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
            response = await client.post(ConfigClass.AUTH_SERVICE + 'invitation-list', json=payload)
        result = response.json()
        if not result.get('result'):
            raise APIException(error_msg='Invite not found', status_code=EAPIResponseCode.not_found.value)
        result['result'] = result['result'][0]
        return JSONResponse(content=result, status_code=response.status_code)

    @router.post(
        '/register/invitation/{invitation_code}',
        summary='Get invitation by invitation code',
    )
    async def post(self, invitation_code: str, data: RegisterPOST):
        payload = {'filters': {'invitation_code': invitation_code, 'status': 'sent'}}
        async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
            response = await client.post(ConfigClass.AUTH_SERVICE + 'invitation-list', json=payload)
        if not response.json()['result']:
            raise APIException(status_code=EAPIResponseCode.not_found.value, error_msg='Invite not found')

        invite = response.json()['result'][0]
        invite_id = invite['id']
        payload = {
            'username': data.username,
            'first_name': data.first_name,
            'last_name': data.last_name,
            'email': invite['email'],
            'password': data.password,
        }
        async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
            response = await client.post(ConfigClass.AUTH_SERVICE + 'admin/users', json=payload)

        if response.status_code != 200:
            error_msg = f'Error creating user: {response.json()}'
            logger.error(error_msg)
            raise APIException(status_code=response.status_code, error_msg=error_msg)

        try:
            template_kwargs = {
                'platform_name': ConfigClass.PROJECT_NAME,
                'username': data.username,
                'login_url': ConfigClass.INVITATION_URL_LOGIN,
                'helpdesk_email': ConfigClass.EMAIL_HELPDESK,
            }
            email_sender = SrvEmail()
            await email_sender.async_send(
                f'Account creation confirmation from {ConfigClass.PROJECT_NAME} Platform',
                [invite['email']],
                msg_type='html',
                template='invitation/confirmation.html',
                template_kwargs=template_kwargs,
            )
        except Exception as e:
            error_msg = f'Error sending email: {e}'
            logger.error(error_msg)
            raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.internal_error.value)

        async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
            invite_response = await client.put(
                ConfigClass.AUTH_SERVICE + f'invitation/{invite_id}', json={'status': 'sent'}
            )
        if invite_response.status_code != 200:
            error_msg = f'Error Updating invite status: {invite_response.json()}'
            logger.error(error_msg)
            raise APIException(status_code=invite_response.status_code, error_msg=error_msg)

        return JSONResponse(content=response.json(), status_code=response.status_code)


@cbv.cbv(router)
class PendingUserRestful:
    current_identity: CurrentUser = Depends(jwt_required)
    project_service_client: ProjectServiceClient = Depends(get_project_service_client)

    @router.post(
        '/invitation-list',
        summary='list invitations',
    )
    async def post(self, request: Request):
        """This method allow to get all pending users from invitation links."""

        logger.info('fetching pending user api triggered')
        my_res = APIResponse()
        post_json = await request.json()

        filters = post_json.get('filters', None)
        project_code = filters.get('project_code', None)

        if self.current_identity['role'] != 'admin':
            project = await self.project_service_client.get(code=project_code)
            if not await has_permission(
                ConfigClass.AUTH_SERVICE, project.code, 'invitation', '*', 'manage', self.current_identity
            ):
                my_res.set_code(EAPIResponseCode.forbidden)
                my_res.set_error_msg('Permission denied')
                return my_res.json_response()
        try:
            response = requests.post(
                ConfigClass.AUTH_SERVICE + 'invitation-list/',
                json=post_json,
                timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT,
            )
        except Exception as e:
            error_msg = f'Error calling Auth service for invite list: {e}'
            logger.error(error_msg)
            raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.internal_error.value)
        return JSONResponse(content=response.json(), status_code=response.status_code)


@cbv.cbv(router)
class ExternalRegistration:
    current_identity: CurrentUser = Depends(jwt_required)

    @router.get('/invitations/external', summary='check if external registration is enabled')
    async def get(self, request: Request):
        async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
            response = await client.get(ConfigClass.AUTH_SERVICE + 'invitations/external')
        return JSONResponse(content=response.json(), status_code=response.status_code)
