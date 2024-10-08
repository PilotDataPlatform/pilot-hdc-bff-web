# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_utils import cbv
from httpx import AsyncClient

from app.auth import jwt_required
from app.components.user.models import CurrentUser
from app.logger import logger
from config import ConfigClass
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode
from services.permissions_service.decorators import DatasetPermission

router = APIRouter(tags=['Dataset Folder'])


@cbv.cbv(router)
class DatasetFolder:
    current_identity: CurrentUser = Depends(jwt_required)

    @router.post(
        '/dataset/{dataset_id}/folder',
        summary='Create empty folder in dataset',
        dependencies=[Depends(DatasetPermission())],
    )
    async def post(self, dataset_id: str, request: Request):
        logger.info('POST dataset folder proxy')
        api_response = APIResponse()
        data = await request.json()
        payload = {'username': self.current_identity['username'], **data}
        try:
            headers = {'Authorization': request.headers.get('Authorization')}
            async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                response = await client.post(
                    ConfigClass.DATASET_SERVICE + f'dataset/{dataset_id}/folder',
                    headers=headers,
                    json=payload,
                )
        except Exception as e:
            logger.info(f'Error calling dataset service: {e}')
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_result(f'Error calling dataset service: {e}')
            return api_response.json_response()
        return JSONResponse(content=response.json(), status_code=response.status_code)
