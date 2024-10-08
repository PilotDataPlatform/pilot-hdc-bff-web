# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import httpx
import requests
from common import has_file_permission
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_utils import cbv

from app.auth import jwt_required
from app.components.exceptions import APIException
from app.components.user.models import CurrentUser
from config import ConfigClass
from models.api_response import EAPIResponseCode
from services.meta import get_entity_by_id
from services.permissions_service.decorators import PermissionsCheck

router = APIRouter(tags=['File Ops'])


@cbv.cbv(router)
class FileActionTasks:
    current_identity: CurrentUser = Depends(jwt_required)

    @router.get(
        '/files/actions/tasks',
        summary='Get task information',
        dependencies=[Depends(PermissionsCheck('project', '*', 'view'))],
    )
    async def get(self, request: Request):
        data = request.query_params
        request_params = {**data}
        request_params.update({'code': request_params.get('project_code')})
        url = ConfigClass.DATAOPS_SERVICE + 'tasks'
        response = requests.get(url, params=request_params, timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT)
        return JSONResponse(content=response.json(), status_code=response.status_code)

    @router.delete(
        '/files/actions/tasks', summary='Delete tasks', dependencies=[Depends(PermissionsCheck('tasks', '*', 'delete'))]
    )
    async def delete(self, request: Request):
        request_body = await request.json()
        url = ConfigClass.DATAOPS_SERVICE + 'tasks'
        response = requests.delete(url, json=request_body, timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT)
        return JSONResponse(content=response.json(), status_code=response.status_code)


@cbv.cbv(router)
class FileActions:
    current_identity: CurrentUser = Depends(jwt_required)

    @router.post(
        '/files/actions',
        summary='invoke an async file operation job',
    )
    async def post(self, request: Request):
        data_actions_utility_url = ConfigClass.DATAOPS_SERVICE + 'files/actions/'
        request_body = await request.json()
        validate_request_params(request_body)
        operation = request_body.get('operation', None)
        session_id = request_body.get('session_id', None)
        if not session_id:
            raise APIException(error_msg='Header Session-ID required', status_code=EAPIResponseCode.forbidden.value)

        payload = {'ids': [item['id'] for item in request_body['payload'].get('targets', [])]}
        async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
            response = await client.get(
                ConfigClass.METADATA_SERVICE + 'items/batch/',
                params=payload,
                timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT,
            )
            if response.status_code != 200:
                raise APIException(
                    error_msg=f'Error getting target data: {response.json()}',
                    status_code=EAPIResponseCode.internal_error.value,
                )
            target_entities = response.json()['result']

        for entity in target_entities:
            if entity['parent'] != request_body['payload']['source']:
                raise APIException(error_msg='Permission denied', status_code=EAPIResponseCode.forbidden.value)
        source_entity = get_entity_by_id(request_body['payload']['source'])
        if not await has_file_permission(
            ConfigClass.AUTH_SERVICE, source_entity, operation.lower(), self.current_identity
        ):
            raise APIException(error_msg='Permission denied', status_code=EAPIResponseCode.forbidden.value)

        payload = request_body
        payload['session_id'] = session_id
        response = requests.post(
            data_actions_utility_url, json=payload, headers=request.headers, timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT
        )
        return JSONResponse(content=response.json(), status_code=response.status_code)


def validate_request_params(request_body: dict):
    if not request_body.get('payload'):
        raise APIException(error_msg="parameter 'payload' required", status_code=EAPIResponseCode.bad_request.value)

    targets = request_body['payload'].get('targets')
    if not targets:
        raise APIException(error_msg='targets required', status_code=EAPIResponseCode.bad_request.value)
    if type(targets) != list:
        raise APIException(
            error_msg='Invalid targets, must be an object list', status_code=EAPIResponseCode.bad_request.value
        )
    if not request_body.get('operation'):
        raise APIException(error_msg='operation required', status_code=EAPIResponseCode.bad_request.value)
    if not request_body.get('project_code'):
        raise APIException(error_msg='project_code required', status_code=EAPIResponseCode.bad_request.value)
