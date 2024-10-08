# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import jwt as pyjwt
import requests
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
from models.api_response import EAPIResponseCode
from services.notifier_services.email_service import SrvEmail
from services.project.client import ProjectServiceClient
from services.project.client import get_project_service_client

router = APIRouter(tags=['Auth'])


@cbv.cbv(router)
class LastLoginRestful:
    @router.put(
        '/users/lastlogin',
        summary="Update user's last login time",
    )
    async def put(self, request: Request):
        try:
            payload = await request.json()
            payload.update({'last_login': True})
            async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                res = await client.put(ConfigClass.AUTH_SERVICE + 'admin/user', json=payload)
            return JSONResponse(content=res.json(), status_code=res.status_code)
        except Exception as e:
            return JSONResponse(content={'result': str(e)}, status_code=403)


@cbv.cbv(router)
class UserStatus:
    @router.get(
        '/user/status',
        summary='Get users status given the email',
    )
    async def get(self, request: Request):
        try:
            token = request.headers.get('Authorization')
            token = token.split()[-1]
            decoded = pyjwt.decode(token, options={'verify_signature': False})
            email = decoded['email']
        except Exception as e:
            return JSONResponse(content={'result': f'JWT user status error {e}'}, status_code=500)

        try:
            payload = {'email': email}
            async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                response = await client.get(ConfigClass.AUTH_SERVICE + 'admin/user', params=payload)
                if not response.json()['result']:
                    return JSONResponse(content='User not found', status_code=404)
            status = response.json()['result']['attributes']['status']
            response_json = response.json()
            result = {
                'email': email,
                'status': status,
            }
            response_json['result'] = result
            return JSONResponse(content=response_json, status_code=response.status_code)
        except Exception as e:
            return JSONResponse(content={'result': f'Error calling auth service {e}'}, status_code=500)


@cbv.cbv(router)
class UserAccount:
    current_identity: CurrentUser = Depends(jwt_required)
    project_service_client: ProjectServiceClient = Depends(get_project_service_client)

    @router.put(
        '/user/account',
        summary='user account mangaement',
    )
    async def put(self, request: Request):
        if self.current_identity['role'] != 'admin':
            return JSONResponse(content={'error_msg': 'forbidden'}, status_code=403)

        try:
            req_body = await request.json()
            operation_type = req_body.get('operation_type', None)
            user_email = req_body.get('user_email', None)
            user_id = req_body.get('user_id', None)
            realm = req_body.get('realm', ConfigClass.KEYCLOAK_REALM)
            operation_payload = req_body.get('payload', {})

            if not operation_type:
                return JSONResponse(content={'result': 'operation_type required.'}, status_code=400)
            if not user_email and not user_id:
                return JSONResponse(content={'result': 'either user_email or user_id required.'}, status_code=400)
            if operation_type not in ['enable', 'disable']:
                return JSONResponse(content={'result': f'operation {operation_type} is not allowed'}, status_code=400)
            payload = {
                'operation_type': operation_type,
                'user_id': user_id,
                'user_email': user_email,
                'realm': realm,
                'payload': operation_payload,
                'operator': self.current_identity['username'],
            }
            async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                response = await client.put(ConfigClass.AUTH_SERVICE + 'user/account', json=payload)

            payload = {'email': user_email}
            async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                response = await client.get(ConfigClass.AUTH_SERVICE + 'admin/user', params=payload)
            user_info = response.json()['result']
            if operation_type == 'enable':
                subject = 'User enabled'
                email_sender = SrvEmail()
                email_sender.send(
                    subject,
                    [user_email],
                    msg_type='html',
                    template='user_actions/enable.html',
                    template_kwargs={
                        'username': user_info.get('username'),
                        'admin_name': self.current_identity['username'],
                        'admin_email': ConfigClass.EMAIL_ADMIN,
                        'support_email': ConfigClass.EMAIL_SUPPORT,
                        'product_name': ConfigClass.PROJECT_NAME,
                    },
                )

                if user_info['role'] == 'admin':
                    logger.info(
                        f'User status is changed to enabled , hence creating namespace folder '
                        f'for: {user_info.get("username")}'
                    )
                    await self.create_usernamespace_folder_admin(username=user_info.get('username'))

            elif operation_type == 'disable':
                subject = 'User disabled'
                email_sender = SrvEmail()
                email_sender.send(
                    subject,
                    [user_email],
                    msg_type='html',
                    template='user_actions/disable.html',
                    template_kwargs={
                        'username': user_info.get('username'),
                        'admin_name': self.current_identity['username'],
                        'admin_email': ConfigClass.EMAIL_ADMIN,
                        'support_email': ConfigClass.EMAIL_SUPPORT,
                        'product_name': ConfigClass.PROJECT_NAME,
                    },
                )
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except Exception as e:
            return JSONResponse(
                content={'result': f'Error calling user account management service {e}'}, status_code=500
            )

    async def create_usernamespace_folder_admin(self, username):
        page = 0
        result = await self.project_service_client.search(page=page, page_size=50)
        projects = result['result']
        while projects:
            result = await self.project_service_client.search(page=page, page_size=50)
            projects = result['result']
            project_codes = [i.code for i in projects]
            page += 1
            self.bulk_create_folder_usernamespace(username, project_codes)

    def bulk_create_folder_usernamespace(self, username: str, project_codes: list):
        try:
            zone_list = ['greenroom', 'core']
            folders = []
            for zone in zone_list:
                for project_code in project_codes:
                    folders.append(
                        {
                            'name': username,
                            'zone': 0 if zone == 'greenroom' else 1,
                            'type': 'name_folder',
                            'owner': username,
                            'container_code': project_code,
                            'container_type': 'project',
                            'size': 0,
                            'location_uri': '',
                            'version': '',
                        }
                    )

            payload = {'items': folders, 'skip_duplicates': True}
            res = requests.post(
                ConfigClass.METADATA_SERVICE + 'items/batch/', json=payload, timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT
            )
            if res.status_code != 200:
                raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=res.json())

        except Exception as e:
            error_msg = f'Error while trying to bulk create namespace folder, error: {e}'
            logger.error(error_msg)
            raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=error_msg)
