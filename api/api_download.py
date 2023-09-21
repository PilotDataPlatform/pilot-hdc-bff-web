# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import requests
from common import has_file_permission
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_utils import cbv

from app.auth import jwt_required
from app.logger import logger
from config import ConfigClass
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode
from services.dataset import get_dataset_by_code
from services.meta import get_entity_by_id

router = APIRouter(tags=['Download'])


@cbv.cbv(router)
class Download:
    current_identity: dict = Depends(jwt_required)

    @router.post(
        '/download/pre',
        summary='Start a file or folder download',
    )
    async def post(self, request: Request):  # noqa: C901
        api_response = APIResponse()
        payload = await request.json()
        zone = 'core'
        if payload.get('container_type') == 'dataset':
            dataset_node = await get_dataset_by_code(payload.get('container_code'))

            for file in payload.get('files'):
                entity_node = get_entity_by_id(file['id'])

            if dataset_node['code'] != entity_node['container_code']:
                logger.error(
                    f"File doesn't belong to dataset file: {dataset_node['code']}, "
                    f"dataset: {entity_node['dataset_code']}"
                )
                api_response.set_code(EAPIResponseCode.forbidden)
                api_response.set_result("File doesn't belong to dataset, Permission denied")
                return api_response.json_response()

            if dataset_node['creator'] != self.current_identity['username']:
                api_response.set_code(EAPIResponseCode.forbidden)
                api_response.set_result('Permission denied')
                return api_response.json_response()
        else:
            for file in payload.get('files'):
                entity_node = get_entity_by_id(file['id'])
                zone = 'greenroom' if entity_node['zone'] == 0 else 'core'

                if not await has_file_permission(
                    ConfigClass.AUTH_SERVICE,
                    entity_node,
                    'download',
                    self.current_identity,
                ):
                    api_response.set_code(EAPIResponseCode.forbidden)
                    api_response.set_error_msg('Permission denied')
                    return api_response.json_response()

        try:
            if zone == 'core':
                response = requests.post(
                    ConfigClass.DOWNLOAD_SERVICE_CORE_V2 + 'download/pre/',
                    json=payload,
                    headers=request.headers,
                    timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT,
                )
            else:
                response = requests.post(
                    ConfigClass.DOWNLOAD_SERVICE_GR_V2 + 'download/pre/',
                    json=payload,
                    headers=request.headers,
                    timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT,
                )
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except Exception as e:
            logger.info(f'Error calling download service {e}')
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_error_msg('Error calling download service')
            return api_response.json_response()


@cbv.cbv(router)
class DatasetDownload:
    current_identity: dict = Depends(jwt_required)

    @router.post(
        '/dataset/download/pre',
        summary='Start a file or folder download in a dataset',
    )
    async def post(self, request: Request):
        api_response = APIResponse()
        payload = await request.json()
        if 'dataset_code' not in payload:
            logger.error('Missing required field dataset_code')
            api_response.set_code(EAPIResponseCode.bad_request)
            api_response.set_error_msg('Missing required field dataset_code')
            return api_response.json_response()

        logger.error('test here for the proxy')

        dataset_node = await get_dataset_by_code(payload.get('dataset_code'))
        if dataset_node['creator'] != self.current_identity['username']:
            api_response.set_code(EAPIResponseCode.forbidden)
            api_response.set_result('Permission denied')
            return api_response.json_response()

        logger.error('test here for the proxy')
        try:
            response = requests.post(
                ConfigClass.DOWNLOAD_SERVICE_CORE_V2 + 'dataset/download/pre',
                json=payload,
                headers=request.headers,
                timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT,
            )
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except Exception as e:
            logger.info(f'Error calling download service {e}')
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_error_msg('Error calling download service')
            return api_response.json_response()
