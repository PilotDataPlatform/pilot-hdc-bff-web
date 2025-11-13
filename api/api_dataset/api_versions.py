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
from fastapi_utils import cbv
from httpx import AsyncClient

from app.auth import jwt_required
from app.components.request.context import RequestContextDependency
from app.components.user.models import CurrentUser
from app.logger import logger
from config import ConfigClass
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode
from services.permissions_service.decorators import DatasetPermission

router = APIRouter(tags=['Dataset Version'])


@cbv.cbv(router)
class Publish:
    current_identity: CurrentUser = Depends(jwt_required)

    @router.post(
        '/dataset/{dataset_id}/publish',
        summary='Publish a new dataset version',
        dependencies=[Depends(DatasetPermission())],
    )
    async def post(self, dataset_id: str, request: Request):
        api_response = APIResponse()
        try:
            headers = {'Authorization': request.headers.get('Authorization')}
            payload = await request.json()
            async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                response = await client.post(
                    ConfigClass.DATASET_SERVICE + f'dataset/{dataset_id}/publish',
                    json=payload,
                    headers=headers,
                )
        except Exception as e:
            logger.info(f'Error calling dataset service: {e}')
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_result(f'Error calling dataset service: {e}')
            return api_response.json_response()
        return JSONResponse(content=response.json(), status_code=response.status_code)


@cbv.cbv(router)
class PublishStatus:
    current_identity: CurrentUser = Depends(jwt_required)

    @router.get(
        '/dataset/{dataset_id}/publish/status',
        summary='Get status of publish',
        dependencies=[Depends(DatasetPermission())],
    )
    async def get(self, dataset_id: str, request: Request):
        api_response = APIResponse()
        try:
            response = requests.get(
                ConfigClass.DATASET_SERVICE + f'dataset/{dataset_id}/publish/status',
                params=request.query_params,
                timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT,
            )
        except Exception as e:
            logger.info(f'Error calling dataset service: {e}')
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_result(f'Error calling dataset service: {e}')
            return api_response.json_response()
        return JSONResponse(content=response.json(), status_code=response.status_code)


@cbv.cbv(router)
class DownloadPre:
    current_identity: CurrentUser = Depends(jwt_required)

    @router.get(
        '/dataset/{dataset_id}/download/pre',
        summary='pre-download for dataset',
        dependencies=[Depends(DatasetPermission())],
    )
    async def get(self, dataset_id: str, request: Request, request_context: RequestContextDependency):
        api_response = APIResponse()
        try:
            response = await request_context.client.get(
                ConfigClass.DATASET_SERVICE + f'dataset/{dataset_id}/download/pre',
                params=request.query_params,
            )
        except Exception as e:
            logger.info(f'Error calling dataset service: {e}')
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_result(f'Error calling dataset service: {e}')
            return api_response.json_response()
        return JSONResponse(content=response.json(), status_code=response.status_code)


@cbv.cbv(router)
class DatasetVersions:
    current_identity: CurrentUser = Depends(jwt_required)

    @router.get(
        '/dataset/{dataset_id}/versions',
        summary='Get dataset versions',
        dependencies=[Depends(DatasetPermission())],
    )
    async def get(self, dataset_id: str, request: Request):
        query_params = dict(request.query_params)
        query_params['dataset_id'] = dataset_id
        async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
            response = await client.get(ConfigClass.DATASET_SERVICE + 'dataset/versions', params=query_params)
        return JSONResponse(content=response.json(), status_code=response.status_code)
