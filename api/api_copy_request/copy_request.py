# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import requests
from common import has_permission
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_utils import cbv

from app.auth import jwt_required
from app.components.user.models import CurrentUser
from config import ConfigClass
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode
from services.permissions_service.decorators import PermissionsCheck

router = APIRouter(tags=['Copy Request'])


@cbv.cbv(router)
class CopyRequest:
    current_identity: CurrentUser = Depends(jwt_required)

    @router.get(
        '/request/copy/{project_code}',
        summary='List copy requests by project_code',
    )
    async def get(self, project_code: str, request: Request):
        api_response = APIResponse()
        data = dict(request.query_params).copy()

        if not await has_permission(
            ConfigClass.AUTH_SERVICE, project_code, 'copyrequest', '*', 'manage', self.current_identity
        ):
            if not await has_permission(
                ConfigClass.AUTH_SERVICE,
                project_code,
                'copyrequest_in_own_namefolder',
                'greenroom',
                'create',
                self.current_identity,
            ):
                api_response.set_error_msg('Permission Denied')
                api_response.set_code(EAPIResponseCode.forbidden)
                return api_response.json_response()
            data['submitted_by'] = self.current_identity['username']

        try:
            response = requests.get(
                ConfigClass.APPROVAL_SERVICE + f'request/copy/{project_code}',
                params=data,
                timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT,
            )
        except Exception as e:
            api_response.set_error_msg(f'Error calling request copy API: {e}')
            return api_response.json_response()
        return JSONResponse(content=response.json(), status_code=response.status_code)

    @router.post(
        '/request/copy/{project_code}',
        summary='Create a copy request',
        dependencies=[Depends(PermissionsCheck('copyrequest_in_own_namefolder', 'greenroom', 'create'))],
    )
    async def post(self, project_code: str, request: Request):
        api_response = APIResponse()
        data = await request.json()

        if self.current_identity['role'] == 'admin':
            api_response.set_code(EAPIResponseCode.forbidden)
            api_response.set_error_msg('Permission denied')
            return api_response.json_response()

        data['submitted_by'] = self.current_identity['username']
        data['project_code'] = project_code
        try:
            response = requests.post(
                ConfigClass.APPROVAL_SERVICE + f'request/copy/{project_code}',
                json=data,
                timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT,
                headers=request.headers,
            )
        except Exception as e:
            api_response.set_error_msg(f'Error calling request copy API: {e}')
            return api_response.json_response()
        return JSONResponse(content=response.json(), status_code=response.status_code)

    @router.put(
        '/request/copy/{project_code}',
        summary='Update a copy request',
        dependencies=[Depends(PermissionsCheck('copyrequest', '*', 'manage'))],
    )
    async def put(self, project_code: str, request: Request):
        api_response = APIResponse()
        data = await request.json()
        put_data = data.copy()
        put_data['username'] = self.current_identity['username']

        try:
            response = requests.put(
                ConfigClass.APPROVAL_SERVICE + f'request/copy/{project_code}',
                json=put_data,
                timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT,
            )
        except Exception as e:
            api_response.set_error_msg(f'Error calling request copy API: {e}')
            return api_response.json_response()
        return JSONResponse(content=response.json(), status_code=response.status_code)


@cbv.cbv(router)
class CopyRequestFiles:
    current_identity: CurrentUser = Depends(jwt_required)

    @router.get(
        '/request/copy/{project_code}/files',
        summary='View a copy requests files',
    )
    async def get(self, project_code: str, request: Request):
        api_response = APIResponse()
        data = request.query_params
        if not await has_permission(
            ConfigClass.AUTH_SERVICE, project_code, 'copyrequest', '*', 'manage', self.current_identity
        ):
            if not await has_permission(
                ConfigClass.AUTH_SERVICE,
                project_code,
                'copyrequest_in_own_namefolder',
                'greenroom',
                'create',
                self.current_identity,
            ):
                api_response.set_error_msg('Permission Denied')
                api_response.set_code(EAPIResponseCode.forbidden)
                return api_response.json_response()

        try:
            response = requests.get(
                ConfigClass.APPROVAL_SERVICE + f'request/copy/{project_code}/files',
                params=data,
                timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT,
            )
        except Exception as e:
            api_response.set_error_msg(f'Error calling request copy API: {e}')
            return api_response.json_response()
        return JSONResponse(content=response.json(), status_code=response.status_code)

    @router.put(
        '/request/copy/{project_code}/files',
        summary='Update file status in a copy request',
        dependencies=[Depends(PermissionsCheck('copyrequest', '*', 'manage'))],
    )
    async def put(self, project_code: str, request: Request):
        api_response = APIResponse()
        data = await request.json()
        post_data = data.copy()
        post_data['username'] = self.current_identity['username']

        try:
            response = requests.put(
                ConfigClass.APPROVAL_SERVICE + f'request/copy/{project_code}/files',
                json=post_data,
                headers=request.headers,
                timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT,
            )
        except Exception as e:
            api_response.set_error_msg(f'Error calling request copy API: {e}')
            return api_response.json_response()
        return JSONResponse(content=response.json(), status_code=response.status_code)

    @router.patch(
        '/request/copy/{project_code}/files',
        summary='Update file status in a copy request',
        dependencies=[Depends(PermissionsCheck('copyrequest', '*', 'manage'))],
    )
    async def patch(self, project_code: str, request: Request):
        api_response = APIResponse()
        data = await request.json()
        post_data = data.copy()
        post_data['username'] = self.current_identity['username']

        try:
            response = requests.patch(
                ConfigClass.APPROVAL_SERVICE + f'request/copy/{project_code}/files',
                json=post_data,
                headers=request.headers,
                timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT,
            )
        except Exception as e:
            api_response.set_error_msg(f'Error calling request copy API: {e}')
            return api_response.json_response()
        return JSONResponse(content=response.json(), status_code=response.status_code)


@cbv.cbv(router)
class CopyRequestPending:
    current_identity: CurrentUser = Depends(jwt_required)

    @router.get(
        '/request/copy/{project_code}/pending-files',
        summary='Get pending files remaining in a copy request',
        dependencies=[Depends(PermissionsCheck('copyrequest', '*', 'manage'))],
    )
    def get(self, project_code: str, request: Request):
        api_response = APIResponse()
        try:
            response = requests.get(
                ConfigClass.APPROVAL_SERVICE + f'request/copy/{project_code}/pending-files',
                params=request.query_params,
                timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT,
            )
        except Exception as e:
            api_response.set_error_msg(f'Error calling request copy API: {e}')
            return api_response.json_response()
        return JSONResponse(content=response.json(), status_code=response.status_code)
