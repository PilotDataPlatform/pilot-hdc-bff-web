# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import httpx
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_utils import cbv

from app.auth import jwt_required
from app.components.user.models import CurrentUser
from config import ConfigClass
from services.permissions_service.decorators import PermissionsCheck

router = APIRouter(tags=['Workbench'])


@cbv.cbv(router)
class WorkspaceRestful:
    current_identity: CurrentUser = Depends(jwt_required)

    @router.get(
        '/guacamole/connection',
        summary='List guacamole connections',
        dependencies=[Depends(PermissionsCheck('workbench', '*', 'view'))],
    )
    async def get(self, request: Request):
        payload = request.query_params
        async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
            response = await client.get(ConfigClass.WORKSPACE_SERVICE + 'guacamole/connection', params=payload)
        return JSONResponse(content=response.json(), status_code=response.status_code)
