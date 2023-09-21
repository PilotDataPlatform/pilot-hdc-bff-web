# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import json

import requests
from common import has_file_permission
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
from services.meta import get_entity_by_id

router = APIRouter(tags=['Tags'])


@cbv.cbv(router)
class TagsAPIV2:
    current_identity: dict = Depends(jwt_required)

    @router.post(
        '/{entity_id}/tags',
        summary='Bulk add or remove tags',
    )
    async def post(self, entity_id: str, request: Request):
        api_response = APIResponse()
        data = await request.json()
        tags = data.get('tags', [])

        if not isinstance(tags, list):
            logger.error('Tags, project_code are required')
            api_response.set_code(EAPIResponseCode.bad_request)
            api_response.set_error_msg('tags, project_code are required.')
            return api_response.json_response()

        entity = get_entity_by_id(entity_id)
        if not await has_file_permission(ConfigClass.AUTH_SERVICE, entity, 'annotate', self.current_identity):
            api_response.set_error_msg('Permission Denied')
            api_response.set_code(EAPIResponseCode.forbidden)
            return api_response.json_response()

        try:
            response = requests.put(
                ConfigClass.METADATA_SERVICE + 'item',
                json=data,
                params={'id': entity_id},
                timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT,
            )
            logger.info(f'Successfully attach tags to entity: {json.dumps(response.json())}')
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except Exception as error:
            logger.error(f'Failed to attach tags to entity {error}')
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_error_msg(str(error))
            return api_response.json_response()
