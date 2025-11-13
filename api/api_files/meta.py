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
from httpx import AsyncClient

from app.auth import jwt_required
from app.components.exceptions import APIException
from app.components.user.models import CurrentUser
from app.logger import logger
from config import ConfigClass
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode
from models.models_item import ItemStatus
from services.permissions_service.decorators import PermissionsCheck

router = APIRouter(tags=['File Meta'])


@cbv.cbv(router)
class FileDetailBulk:
    current_identity: CurrentUser = Depends(jwt_required)

    @router.post(
        '/files/bulk/detail',
        summary='Bulk get files from list of ids',
    )
    async def post(self, request: Request):
        api_response = APIResponse()
        data = await request.json()
        payload = {'ids': data.get('ids', [])}
        response = requests.get(
            ConfigClass.METADATA_SERVICE + 'items/batch', params=payload, timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT
        )
        if response.status_code != 200:
            return JSONResponse(content=response.json(), status_code=response.status_code)
        file_node = response.json()['result']

        for file_node in response.json()['result']:
            if not await has_file_permission(ConfigClass.AUTH_SERVICE, file_node, 'view', self.current_identity):
                api_response.set_code(EAPIResponseCode.forbidden)
                api_response.set_error_msg('Permission denied')
                return api_response.json_response()
        result = response.json()
        for entity in result['result']:
            entity['zone'] = 'greenroom' if entity['zone'] == 0 else 'core'
        return JSONResponse(content=result, status_code=response.status_code)


@cbv.cbv(router)
class FileMeta:
    current_identity: CurrentUser = Depends(jwt_required)

    @router.get(
        '/files/meta',
        summary='List files in project or folder',
        dependencies=[Depends(PermissionsCheck('project', '*', 'view'))],
    )
    async def get(self, request: Request):  # noqa: C901
        """Proxy for entity info file META API, handles permission checks."""
        api_response = APIResponse()
        logger.info('Call API for fetching file info')

        page_size = int(request.query_params.get('page_size', 25))
        page = int(request.query_params.get('page', 0))
        order_by = request.query_params.get('order_by', 'created_time')
        order_type = request.query_params.get('order_type', 'desc')
        zone = request.query_params.get('zone', '')
        project_code = request.query_params.get('project_code', '')
        parent_path = request.query_params.get('parent_path', '')
        restore_path = request.query_params.get('restore_path', '')
        source_type = request.query_params.get('source_type', '')
        name = request.query_params.get('name', '')
        owner = request.query_params.get('owner', '')
        status = request.query_params.get('status', ItemStatus.ACTIVE)

        if source_type not in ['trash', 'project', 'folder', 'collection']:
            logger.error('Invalid zone')
            api_response.set_code(EAPIResponseCode.bad_request)
            api_response.set_error_msg('Invalid zone')
            return api_response.json_response()
        if zone not in ['greenroom', 'core', 'all']:
            logger.error('Invalid zone')
            api_response.set_code(EAPIResponseCode.bad_request)
            api_response.set_error_msg('Invalid zone')
            return api_response.json_response()

        if zone == 'greenroom':
            zone_num = 0
        elif zone == 'core':
            zone_num = 1
        else:
            zone_num = None

        payload = {
            'page': page,
            'page_size': page_size,
            'order': order_type,
            'sorting': order_by,
            'container_code': project_code,
            'recursive': False,
            'fav_user': self.current_identity['username'],
            'status': status,
        }
        if zone_num is not None:
            payload['zone'] = zone_num
        if name:
            payload['name'] = (name.replace('%', r'\%') + '%',)  # noqa: W605
        if owner:
            payload['owner'] = (owner.replace('%', r'\%') + '%',)  # noqa: W605
        if source_type == 'folder':
            if restore_path:
                payload['restore_path'] = restore_path
            payload['parent_path'] = parent_path
        elif source_type == 'project':
            payload['parent_path'] = None
        elif source_type == 'collection':
            collection_id = request.query_params.get('parent_id')
            if not collection_id:
                api_response.set_code(EAPIResponseCode.bad_request)
                api_response.set_error_msg('parent_id required for collection')
                return api_response.json_response()
            payload['id'] = collection_id
        elif source_type == 'trash':
            payload['status'] = ItemStatus.ARCHIVED

        if source_type == 'collection':
            url = ConfigClass.METADATA_SERVICE + 'collection/items/'
        else:
            url = ConfigClass.METADATA_SERVICE + 'items/search/'
        headers = {'Authorization': request.headers.get('Authorization')}
        async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
            response = await client.get(url, params=payload, headers=headers)
        if response.status_code != 200:
            error_msg = f'Error calling Meta service get_node_by_id: {response.json()}'
            raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.internal_error.value)
        result = response.json()
        for entity in result['result']:
            entity['zone'] = 'greenroom' if entity['zone'] == 0 else 'core'
        return JSONResponse(content=result, status_code=response.status_code)
