# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import requests
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi import Response
from fastapi.responses import JSONResponse
from fastapi_utils import cbv

from app.auth import jwt_required
from app.logger import logger
from config import ConfigClass
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode
from services.dataset import get_dataset_by_id
from services.meta import get_entity_by_id

router = APIRouter(tags=['Preview'])


@cbv.cbv(router)
class Preview:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/{file_id}/preview/',
        summary='Preview a file',
    )
    async def get(self, file_id: str, request: Request):
        logger.info('GET preview called in bff')
        api_response = APIResponse()

        data = request.query_params
        dataset_id = data.get('dataset_geid')
        dataset_node = await get_dataset_by_id(dataset_id)
        file_node = get_entity_by_id(file_id)

        if dataset_node['code'] != file_node['container_code']:
            api_response.set_code(EAPIResponseCode.forbidden)
            api_response.set_result("File doesn't belong to dataset, Permission denied")
            return api_response.json_response()

        if dataset_node['creator'] != self.current_identity['username']:
            api_response.set_code(EAPIResponseCode.forbidden)
            api_response.set_result('Permission denied')
            return api_response.json_response()

        try:
            response = requests.get(
                ConfigClass.DATASET_SERVICE + f'{file_id}/preview',
                params=data,
                headers=request.headers,
                timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT,
            )
        except Exception as e:
            logger.info(f'Error calling dataops gr: {e}')
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_result(f'Error calling dataops gr: {e}')
            return api_response.json_response()
        return JSONResponse(content=response.json(), status_code=response.status_code)


@cbv.cbv(router)
class StreamPreview:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/{file_id}/preview/stream',
        summary='Preview a file with streaming response',
    )
    async def get(self, file_id: str, request: Request):
        logger.info('GET preview called in bff')
        api_response = APIResponse()

        data = request.query_params
        dataset_id = data.get('dataset_geid')
        dataset_node = await get_dataset_by_id(dataset_id)
        file_node = get_entity_by_id(file_id)

        if dataset_node['code'] != file_node['container_code']:
            logger.error(f"File doesn't belong to dataset file: {file_id}, dataset: {dataset_id}")
            api_response.set_code(EAPIResponseCode.forbidden)
            api_response.set_result("File doesn't belong to dataset, Permission denied")
            return api_response.json_response()

        if dataset_node['creator'] != self.current_identity['username']:
            api_response.set_code(EAPIResponseCode.forbidden)
            api_response.set_result('Permission denied')
            return api_response.json_response()

        try:
            response = requests.get(
                ConfigClass.DATASET_SERVICE + f'{file_id}/preview/stream',
                params=data,
                stream=True,
                timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT,
            )
            return Response(
                content=response.iter_content(chunk_size=10 * 1025),
                media_type=response.headers.get('Content-Type', 'text/plain'),
            )
        except Exception as e:
            logger.info(f'Error calling dataset service: {e}')
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_result(f'Error calling dataops gr: {e}')
            return api_response.json_response()
