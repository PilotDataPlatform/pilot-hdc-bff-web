# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Annotated

import httpx
from fastapi import APIRouter
from fastapi import Depends
from fastapi.responses import JSONResponse
from fastapi_utils import cbv

from app.auth import jwt_required
from app.components.user.models import CurrentUser
from app.logger import logger
from config import ConfigClass
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode
from models.bridge import AddVisits
from models.bridge import AddVisitsResponse
from models.bridge import GetRecentVisits
from services.bridge import BridgeService
from services.bridge import get_bridge_service

router = APIRouter(tags=['Bridge'])


@cbv.cbv(router)
class Bridge:

    current_identity: CurrentUser = Depends(jwt_required)

    @router.post('/visits', summary='Compute one visit to the user from JWT', response_model=AddVisitsResponse)
    async def add_visit(self, bridge_service: Annotated[BridgeService, Depends(get_bridge_service)], data: AddVisits):
        username = self.current_identity['username']
        response = AddVisitsResponse(result='success', code=EAPIResponseCode.success.value)

        await bridge_service.add_visit(data.entity, data.code, username)
        return JSONResponse(content=response.dict(), status_code=response.code)

    @router.get('/visits', summary='get JWT user last visits')
    async def get_visit(
        self, bridge_service: Annotated[BridgeService, Depends(get_bridge_service)], params: GetRecentVisits = Depends()
    ):
        username = self.current_identity['username']
        entity = params.entity
        last_codes = await bridge_service.get_visits(params.entity, username, params.last)
        logger.info(f'got last codes {last_codes}')
        if not last_codes:
            res = APIResponse()
            res.set_result([])

            return res.json_response()

        if entity == 'project':
            url = f'{ConfigClass.PROJECT_SERVICE}/v1/projects/'
        else:
            url = f'{ConfigClass.DATASET_SERVICE}datasets/'

        async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
            response = await client.get(url, params={'code_any': ','.join(last_codes)})
        content = response.json()

        if response.status_code == 200:
            content['result'] = await bridge_service.sort_result_by_visit_codes_order(last_codes, content['result'])

        return JSONResponse(content=content, status_code=response.status_code)
