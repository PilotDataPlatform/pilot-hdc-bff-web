# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Annotated
from typing import ClassVar
from uuid import UUID
from uuid import uuid4

import httpx
from common import has_file_permission
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Header
from fastapi import Response
from fastapi_utils import cbv
from pydantic import BaseModel

from api.api_dataset_rest_proxy import ProxyPass
from app.auth import jwt_required
from app.components.exceptions import APIException
from app.components.user.models import CurrentUser
from app.logger import logger
from config import Settings
from config import get_settings
from models.api_response import EAPIResponseCode
from services.meta import async_get_entity_by_id

router = APIRouter(tags=['Central Node'])


class InitFileUploadSchema(BaseModel):
    file_id: UUID
    session_id: str


@cbv.cbv(router)
class CopyToCentralNode(ProxyPass):
    request_allowed_parameters: ClassVar[set[str]] = set()
    response_allowed_headers: ClassVar[set[str]] = {'Content-Type'}

    current_user: CurrentUser = Depends(jwt_required)
    settings: Settings = Depends(get_settings)

    @router.post('/central-node/upload', summary='Initiate file upload to the Central Node.')
    async def init(self, body: InitFileUploadSchema) -> Response:
        file_node = await async_get_entity_by_id(str(body.file_id))
        if not await has_file_permission(self.settings.AUTH_SERVICE, file_node, 'copy', self.current_user):
            raise APIException(error_msg='Permission denied', status_code=EAPIResponseCode.forbidden.value)

        file_id = file_node['id']
        project_code = file_node['container_code']
        job_id = str(uuid4())
        session_id = body.session_id
        logger.info(
            f'Init a file upload to central node for file_id: {file_id}, job_id: {job_id}, session_id: {session_id}'
        )
        async with httpx.AsyncClient(timeout=self.settings.CENTRAL_NODE_CLIENT_TIMEOUT_SECONDS) as client:
            raw_response = await client.post(
                f'{self.settings.DATAOPS_SERVICE}central-node/upload',
                data={
                    'file_id': file_id,
                    'project_code': project_code,
                    'job_id': job_id,
                    'session_id': session_id,
                    'operator': self.current_user.username,
                },
            )

        return await self.process_response(raw_response)

    @router.get('/central-node/upload/{upload_key}', summary='Wait file upload authorization from the Central Node.')
    async def wait(self, upload_key: str, authorization: Annotated[str | None, Header()] = None) -> Response:
        if authorization is None:
            raise APIException(error_msg='Missing Authorization header.', status_code=EAPIResponseCode.forbidden.value)

        async with httpx.AsyncClient(timeout=self.settings.CENTRAL_NODE_PULL_CLIENT_TIMEOUT_SECONDS) as client:
            raw_response = await client.get(
                f'{self.settings.DATAOPS_SERVICE}central-node/upload/{upload_key}',
                headers={'Authorization': authorization},
            )

        return await self.process_response(raw_response)
