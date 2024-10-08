# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from common import has_file_permission
from fastapi import APIRouter
from fastapi import Depends
from fastapi.responses import JSONResponse
from fastapi_utils import cbv
from httpx import AsyncClient

from app.auth import jwt_required
from app.components.user.models import CurrentUser
from app.logger import logger
from config import ConfigClass
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode

router = APIRouter(tags=['Archive'])


@cbv.cbv(router)
class Archive:
    current_identity: CurrentUser = Depends(jwt_required)

    @router.get(
        '/archive',
        summary='Get a zip preview given file id',
    )
    async def get(self, file_id: str):
        logger.info('GET archive called in bff')
        api_response = APIResponse()
        async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
            request = await client.get(f'{ConfigClass.METADATA_SERVICE}item/{file_id}/')
        file_response = request.json()['result']
        if not file_response:
            logger.error(f'File not found with following id: {file_id}')
            api_response.set_code(EAPIResponseCode.not_found)
            api_response.set_result('File not found')
            return api_response.json_response()

        if not await has_file_permission(ConfigClass.AUTH_SERVICE, file_response, 'view', self.current_identity):
            api_response.set_code(EAPIResponseCode.forbidden)
            api_response.set_result('Permission denied')
            return api_response.json_response()

        try:
            async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                response = await client.get(ConfigClass.DATAOPS_SERVICE + 'archive', params={'file_id': file_id})
        except Exception as e:
            logger.info(f'Error calling dataops gr: {e}')
            return JSONResponse(content=response.json(), status_code=response.status_code)
        return JSONResponse(content=response.json(), status_code=response.status_code)
