# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import requests
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.responses import Response
from fastapi_utils import cbv

from app.auth import jwt_required
from app.components.user.models import CurrentUser
from app.logger import logger
from config import ConfigClass
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode
from services.permissions_service.decorators import DatasetPermission

router = APIRouter(tags=['Dataset Schema'])


@cbv.cbv(router)
class SchemaCreate:
    current_identity: CurrentUser = Depends(jwt_required)

    @router.post(
        '/dataset/{dataset_id}/schema',
        summary='Create a new schema',
        dependencies=[Depends(DatasetPermission())],
    )
    async def post(self, dataset_id: str, request: Request):
        api_response = APIResponse()
        try:
            response = requests.post(
                ConfigClass.DATASET_SERVICE + 'schema',
                json=await request.json(),
                timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT,
            )
        except Exception as e:
            logger.info(f'Error calling dataset service: {e}')
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_result(f'Error calling dataset service: {e}')
            return api_response.json_response()
        return JSONResponse(content=response.json(), status_code=response.status_code)


@cbv.cbv(router)
class Schema:
    current_identity: CurrentUser = Depends(jwt_required)

    @router.put(
        '/dataset/{dataset_id}/schema/{schema_id}',
        summary='Update a schema',
        dependencies=[Depends(DatasetPermission())],
    )
    async def put(self, dataset_id: str, schema_id: str, request: Request):
        api_response = APIResponse()
        payload = await request.json()
        payload['username'] = self.current_identity['username']
        try:
            response = requests.put(
                ConfigClass.DATASET_SERVICE + f'schema/{schema_id}',
                json=payload,
                timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT,
            )
        except Exception as e:
            logger.info(f'Error calling dataset service: {e}')
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_result(f'Error calling dataset service: {e}')
            return api_response.json_response()
        return JSONResponse(content=response.json(), status_code=response.status_code)

    @router.get(
        '/dataset/{dataset_id}/schema/{schema_id}',
        summary='Get a schema by id',
        dependencies=[Depends(DatasetPermission())],
    )
    async def get(self, dataset_id: str, schema_id: str):
        api_response = APIResponse()

        try:
            response = requests.get(
                ConfigClass.DATASET_SERVICE + f'schema/{schema_id}', timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT
            )
        except Exception as e:
            logger.info(f'Error calling dataset service: {e}')
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_result(f'Error calling dataset service: {e}')
            return api_response.json_response()
        return JSONResponse(content=response.json(), status_code=response.status_code)

    @router.delete(
        '/dataset/{dataset_id}/schema/{schema_id}',
        summary='Delete a schema by id',
        dependencies=[Depends(DatasetPermission())],
    )
    async def delete(self, dataset_id: str, schema_id: str, request: Request):
        api_response = APIResponse()
        payload = {'username': self.current_identity['username'], 'dataset_geid': dataset_id, 'activity': []}
        try:
            response = requests.delete(
                ConfigClass.DATASET_SERVICE + f'schema/{schema_id}',
                json=payload,
                timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT,
            )
        except Exception as e:
            logger.info(f'Error calling dataset service: {e}')
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_result(f'Error calling dataset service: {e}')
            return api_response.json_response()
        return Response(status_code=response.status_code)


@cbv.cbv(router)
class SchemaList:
    current_identity: CurrentUser = Depends(jwt_required)

    @router.post(
        '/dataset/{dataset_id}/schema/list',
        summary='List schemas',
        dependencies=[Depends(DatasetPermission())],
    )
    async def post(self, dataset_id: str, request: Request):
        api_response = APIResponse()
        payload = await request.json()
        payload['dataset_geid'] = dataset_id
        try:
            response = requests.post(
                ConfigClass.DATASET_SERVICE + 'schema/list', json=payload, timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT
            )
        except Exception as e:
            logger.info(f'Error calling dataset service: {e}')
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_result(f'Error calling dataset service: {e}')
            return api_response.json_response()
        return JSONResponse(content=response.json(), status_code=response.status_code)
