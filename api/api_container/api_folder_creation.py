# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import httpx
from common import has_permission
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_utils import cbv

from app.auth import jwt_required
from app.components.user.models import CurrentUser
from config import ConfigClass
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode
from models.models_item import ItemStatus
from services.meta import search_entities

router = APIRouter(tags=['Folder Create'])


@cbv.cbv(router)
class FolderCreation:
    current_identity: CurrentUser = Depends(jwt_required)

    @router.post(
        '/containers/{project_id}/folder',
        summary='Create a folder in a project',
    )
    async def post(self, project_id: str, request: Request):
        api_response = APIResponse()
        data = await request.json()
        folder_name = data.get('folder_name')
        project_code = data.get('project_code')
        zone = data.get('zone')
        zone = 0 if zone == 'greenroom' else 1
        parent_path = data.get('parent_path')
        parent_entity = None
        entity_type = 'folder'

        if not parent_path:
            entity_type = 'name_folder'
            if not await has_permission(
                ConfigClass.AUTH_SERVICE,
                project_code,
                'file_in_own_namefolder',
                data.get('zone').lower(),
                'view',
                self.current_identity,
            ):
                api_response.set_code(EAPIResponseCode.forbidden)
                api_response.set_error_msg('Permission denied')
                return api_response.json_response()
        else:
            search_parent_path = '/'.join(parent_path.split('/')[:-1])
            name = ''.join(parent_path.split('/')[-1])
            headers = {'Authorization': request.headers.get('Authorization')}
            parent_entity = await search_entities(project_code, search_parent_path, zone, headers, name=name)
            parent_entity = parent_entity[0]
            if not parent_entity:
                api_response.set_code(EAPIResponseCode.forbidden)
                api_response.set_error_msg('Permission denied')
                return api_response.json_response()

        if len(folder_name) < 1 or len(folder_name) > 20:
            api_response.set_code(EAPIResponseCode.bad_request)
            api_response.set_error_msg('Folder should be 1 to 20 characters')
            return api_response.json_response()

        payload = {
            'name': folder_name,
            'zone': zone,
            'type': entity_type,
            'status': ItemStatus.ACTIVE,
            'owner': self.current_identity['username'],
            'container_code': project_code,
            'container_type': 'project',
            'size': 0,
            'location_uri': '',
            'version': '',
        }
        if parent_entity:
            payload['parent'] = parent_entity['id']
            if parent_entity.get('parent_path'):
                payload['parent_path'] = parent_entity['parent_path'] + '/' + parent_entity['name']
            else:
                payload['parent_path'] = parent_entity['name']

        with httpx.Client(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
            response = client.post(ConfigClass.METADATA_SERVICE + 'item/', json=payload)
        return JSONResponse(content=response.json(), status_code=response.status_code)
