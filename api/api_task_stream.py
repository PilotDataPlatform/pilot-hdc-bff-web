# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import httpx
from fastapi import APIRouter
from fastapi import Depends
from fastapi.responses import JSONResponse
from fastapi_utils import cbv

from app.auth import jwt_required
from app.components.user.models import CurrentUser
from config import ConfigClass

router = APIRouter(tags=['Task stream'])


@cbv.cbv(router)
class TaskStream:
    current_identity: CurrentUser = Depends(jwt_required)

    @router.delete(
        '/task-stream',
        summary='Delete a user\'s old file status events',
    )
    async def call_delete_task_stream(self) -> JSONResponse:
        """Delete a user's old file status events."""
        url = ConfigClass.DATAOPS_SERVICE + 'task-stream/'
        params = {'user': self.current_identity['username']}
        async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
            response = await client.delete(url, params=params)
        return JSONResponse(content=response.json(), status_code=response.status_code)
