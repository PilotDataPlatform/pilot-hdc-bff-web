# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import requests
from common import has_file_permission
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_utils import cbv

from app.auth import jwt_required
from app.components.user.models import CurrentUser
from app.logger import logger
from config import ConfigClass
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode
from services.meta import get_entities_batch
from services.meta import search_entities

from .utils import get_new_tags

router = APIRouter(tags=['Tags'])


@cbv.cbv(router)
class BatchTagsAPIV2:
    current_identity: CurrentUser = Depends(jwt_required)

    @router.post(
        '/entity/tags',
        summary='Bulk add or remove tags',
    )
    async def post(self, request: Request):  # noqa: C901
        api_response = APIResponse()
        data = await request.json()
        only_files = data.get('only_files', False)
        inherit = data.get('inherit', False)
        entity_ids = data.get('entity', [])
        tags = data.get('tags')
        operation = data.get('operation')
        entities = get_entities_batch(entity_ids)
        update_payload = {
            'items': [],
        }
        params = {'ids': []}
        for entity in entities:
            if not await has_file_permission(ConfigClass.AUTH_SERVICE, entity, 'annotate', self.current_identity):
                api_response.set_error_msg('Permission Denied')
                api_response.set_code(EAPIResponseCode.forbidden)
                return api_response.json_response()

            if inherit:
                if entity['type'] == 'folder':
                    headers = {'Authorization': request.headers.get('Authorization')}
                    child_entities = await search_entities(
                        entity['container_code'],
                        entity['parent_path'] + '/' + entity['name'],
                        entity['zone'],
                        headers,
                        recursive=True,
                    )
                    for child_entity in child_entities:
                        if only_files and child_entity['type'] == 'folder':
                            continue

                        update_payload['items'].append(
                            {
                                'tags': get_new_tags(operation, child_entity, tags),
                            }
                        )
                        params['ids'].append(child_entity['id'])
            if only_files and entity['type'] == 'folder':
                continue

            update_payload['items'].append(
                {
                    'tags': get_new_tags(operation, entity, tags),
                }
            )
            params['ids'].append(entity['id'])

        if not update_payload['items']:
            api_response.set_result('None updated')
            return api_response.json_response()

        try:
            response = requests.put(
                ConfigClass.METADATA_SERVICE + 'items/batch',
                json=update_payload,
                params=params,
                timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT,
            )
            logger.info(f'Batch operation result: {response}')
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except Exception as error:
            logger.error(f'Error while performing batch operation for tags : {error}')
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_result('Error while performing batch operation for tags ' + str(error))
            return api_response.json_response()
