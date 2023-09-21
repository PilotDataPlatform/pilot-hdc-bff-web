# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import os
from datetime import datetime

from common import has_permission
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_utils import cbv
from httpx import AsyncClient
from httpx import ReadTimeout

from app.auth import jwt_required
from app.components.exceptions import APIException
from app.logger import logger
from config import ConfigClass
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode

router = APIRouter(tags=['Users'])


@cbv.cbv(router)
class UserRestful:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/users/{username}',
        summary='Get user by username',
    )
    async def get(self, username: str, request: Request):
        api_response = APIResponse()
        project_code = request.query_params.get('project_code')

        if self.current_identity['username'] != username:
            if not await has_permission(
                ConfigClass.AUTH_SERVICE, project_code, 'users', '*', 'manage', self.current_identity
            ):
                api_response.set_error_msg("Username doesn't match current user")
                api_response.set_code(EAPIResponseCode.forbidden)
                return api_response.json_response()

        auth_debug_request_id = os.urandom(16).hex()
        data = {
            'username': username,
            '_auth_debug_request_id': auth_debug_request_id,
        }
        async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
            try:
                response = await client.get(ConfigClass.AUTH_SERVICE + 'admin/user', params=data)
            except ReadTimeout:
                logger.warning(
                    f'Timeout while requesting auth service with _auth_debug_request_id: {auth_debug_request_id}'
                )
                raise

        if not response.json():
            api_response.set_error_msg('User not found')
            api_response.set_code(EAPIResponseCode.not_found)
            return api_response.json_response()
        response_json = response.json()['result']
        response_json['name'] = response_json['username']
        for key, value in response_json['attributes'].items():
            if 'announcement_' in key:
                response_json[key] = value

        create_time = response_json['createdTimestamp']
        create_time = datetime.fromtimestamp(int(create_time / 1000)).strftime('%Y-%m-%dT%H:%M:%S')
        response_json['createdTimestamp'] = create_time

        api_response.set_result(response_json)
        api_response.set_code(response.status_code)
        return api_response.json_response()

    @router.put(
        '/users/{username}',
        summary='Update user by username',
    )
    async def put(self, username: str, request: Request):
        api_response = APIResponse()
        data = await request.json()
        if self.current_identity['username'] != username:
            api_response.set_error_msg("Username doesn't match current user")
            api_response.set_code(EAPIResponseCode.forbidden)
            return api_response.json_response()
        if len(data.items()) > 1:
            api_response.set_error_msg('Ton many parameters, only 1 announcement can be updated')
            api_response.set_code(EAPIResponseCode.bad_request)
            return api_response.json_response()

        for key, value in data.items():
            if 'announcement' not in key:
                api_response.set_error_msg('Invalid field, must have a announcement_ prefix')
                api_response.set_code(EAPIResponseCode.bad_request)
                return api_response.json_response()
            payload = {
                'project_code': key.replace('announcement_', ''),
                'announcement_pk': value,
                'username': username,
            }
        async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
            response = await client.put(ConfigClass.AUTH_SERVICE + 'admin/user', json=payload)
        return JSONResponse(content=response.json(), status_code=response.status_code)


async def is_user_in_project(username: str, project_code: str) -> bool:

    async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
        response = await client.get(
            ConfigClass.AUTH_SERVICE + 'admin/users/realm-roles',
            params={'username': username},
        )
    if response.status_code != 200:
        error_msg = 'Error getting user from auth service: {response.json()}'
        raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=error_msg)

    user_roles = response.json().get('result', [])
    user_project_role = None
    for role in user_roles:
        if project_code in role.get('name'):
            user_project_role = role['name']
            break
    if not user_project_role:
        return False
    return True
