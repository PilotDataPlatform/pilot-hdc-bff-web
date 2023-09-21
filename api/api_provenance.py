# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import requests
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_utils import cbv

from app.auth import jwt_required
from config import ConfigClass

router = APIRouter(tags=['Provenance'])


@cbv.cbv(router)
class DataLineage:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/lineage',
        summary='Lineage',
    )
    async def get(self, request: Request):
        url = ConfigClass.PROVENANCE_SERVICE + 'lineage/'
        response = requests.get(url, params=request.query_params, timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT)
        return JSONResponse(content=response.json(), status_code=response.status_code)
