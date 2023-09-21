# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from common import ProjectClient
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_utils import cbv
from httpx import AsyncClient

from app.auth import jwt_required
from config import ConfigClass

router = APIRouter(tags=['User Event'])


@cbv.cbv(router)
class Event:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/user/events',
        summary='List user events',
    )
    async def get(self, request: Request):
        """List user events."""
        async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
            event_response = await client.get(ConfigClass.AUTH_SERVICE + 'events', params=request.query_params)
        event_response_json = event_response.json()
        events = event_response.json()['result']
        project_codes = [i['detail']['project_code'] for i in events if 'project_code' in i['detail']]

        projects = []
        for code in project_codes:
            project_client = ProjectClient(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
            project = await project_client.get(code=code)
            projects.append(await project.json())

        for event in events:
            for project in projects:
                if project['code'] == event['detail'].get('project_code'):
                    event['detail']['project_name'] = project['name']
        event_response_json['result'] = events
        return JSONResponse(content=event_response_json, status_code=event_response.status_code)
