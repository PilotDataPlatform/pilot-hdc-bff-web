# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import httpx
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
from services.permissions_service.decorators import PermissionsCheck

router = APIRouter(tags=['Permissions'])


@cbv.cbv(router)
class Permissions:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/permissions/metadata',
        summary='Get permission metadata proxy',
        dependencies=[Depends(PermissionsCheck('project', '*', 'view'))],
    )
    async def list_metadata(self, request: Request):
        api_response = APIResponse()
        logger.info('List permissions metadata called')
        try:
            async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                url = ConfigClass.AUTH_SERVICE + 'permissions/metadata'
                response = await client.get(url, params=request.query_params)
                return JSONResponse(content=response.json(), status_code=response.status_code)
        except Exception as e:
            error_msg = f'Error calling list permissions metadata API: {e}'
            logger.error(error_msg)
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_result(error_msg)
            return api_response.json_response()
