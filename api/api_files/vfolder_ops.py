# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import json

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_utils import cbv
from httpx import AsyncClient

from app.auth import jwt_required
from app.logger import logger
from config import ConfigClass
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode
from services.permissions_service.decorators import PermissionsCheck

from .utils import get_collection_by_id

router = APIRouter(tags=['Collections'])


@cbv.cbv(router)
class VirtualFolderFiles:
    current_identity: dict = Depends(jwt_required)

    @router.post(
        '/collections/{collection_id}/files',
        summary='Get items from vfolder',
    )
    async def post(self, collection_id: str, request: Request):
        """Add items to vfolder."""
        _res = APIResponse()

        try:
            vfolder = get_collection_by_id(collection_id)
            if self.current_identity['role'] != 'admin':
                if vfolder['owner'] != self.current_identity['username']:
                    _res.set_code(EAPIResponseCode.bad_request)
                    _res.set_result('no permission for this project')
                    return _res.json_response()

            data = await request.json()
            data['id'] = collection_id
            url = f'{ConfigClass.METADATA_SERVICE}collection/items/'
            async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                response = await client.post(url, json=data)
            if response.status_code != 200:
                logger.error(f'Failed to add items to collection: {response.text}')
                _res.set_code(EAPIResponseCode.internal_error)
                _res.set_result('Failed to add items to collection')
                return _res.json_response()
            else:
                logger.info(f'Successfully add items to collection: {json.dumps(response.json())}')
                return response.json()

        except Exception as e:
            logger.error(f'errors in add items to collection: {e}')
            _res.set_code(EAPIResponseCode.internal_error)
            _res.set_result('Failed to add items to collection')
            return _res.json_response()

    @router.delete(
        '/collections/{collection_id}/files',
        summary='Remove items from vfolder',
    )
    async def delete(self, collection_id: str, request: Request):
        """Delete items from vfolder."""

        _res = APIResponse()

        try:
            vfolder = get_collection_by_id(collection_id)
            if self.current_identity['role'] != 'admin':
                if vfolder['owner'] != self.current_identity['username']:
                    _res.set_code(EAPIResponseCode.bad_request)
                    _res.set_result('no permission for this project')
                    return _res.json_response()

            data = await request.json()
            data['id'] = collection_id
            url = f'{ConfigClass.METADATA_SERVICE}collection/items/'
            async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                response = await client.request(url=url, method='DELETE', json=data)
            if response.status_code != 200:
                logger.error(f'Failed to remove items from collection: {response.text}')
                _res.set_code(EAPIResponseCode.internal_error)
                _res.set_result('Failed to remove items from collection')
                return _res.json_response()

            else:
                logger.info(f'Successfully remove items from collection: {json.dumps(response.json())}')
                return response.json()

        except Exception as e:
            logger.error(f'errors in remove items from collection: {e}')
            _res.set_code(EAPIResponseCode.internal_error)
            _res.set_result('Failed to remove items from collection')
            return _res.json_response()

    @router.get(
        '/collections/{collection_id}/files',
        summary='get items from vfolder',
    )
    async def get(self, collection_id: str):

        """Get items from vfolder."""
        _res = APIResponse()

        try:
            vfolder = get_collection_by_id(collection_id)
            if self.current_identity['role'] != 'admin':
                if vfolder['owner'] != self.current_identity['username']:
                    _res.set_code(EAPIResponseCode.bad_request)
                    _res.set_result('no permission for this project')
                    return _res.json_response()

            url = f'{ConfigClass.METADATA_SERVICE}collection/items/'
            params = {'id': collection_id}
            async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                response = await client.get(url, params=params)
            if response.status_code != 200:
                logger.error(f'Failed to get items from collection: {response.text}')
                _res.set_code(EAPIResponseCode.internal_error)
                _res.set_result('Failed to get items from collection')
                return _res.json_response()
            else:
                logger.info(f'Successfully retrieved items from collection: {json.dumps(response.json())}')
                return response.json()

        except Exception as e:
            logger.error(f'errors in retrieve items to collection: {e}')
            _res.set_code(EAPIResponseCode.internal_error)
            _res.set_result('Failed to retrieve items from collection')
            return _res.json_response()


@cbv.cbv(router)
class VirtualFolder:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/collections',
        summary='Get collections',
        dependencies=[Depends(PermissionsCheck('collections', 'core', 'manage'))],
    )
    async def get(self, request: Request):
        payload = {
            'owner': self.current_identity['username'],
            'container_code': request.query_params.get('project_code'),
        }
        async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
            response = await client.get(f'{ConfigClass.METADATA_SERVICE}collection/search/', params=payload)
        return JSONResponse(content=response.json(), status_code=response.status_code)

    @router.post(
        '/collections',
        summary='Create collection',
        dependencies=[Depends(PermissionsCheck('collections', 'core', 'manage'))],
    )
    async def post(self, request: Request):
        data = await request.json()
        payload = {
            'owner': self.current_identity['username'],
            **data,
            'container_code': request.query_params.get('project_code'),
        }
        payload['container_code'] = payload.pop('project_code')
        async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
            response = await client.post(f'{ConfigClass.METADATA_SERVICE}collection/', json=payload)
        return JSONResponse(content=response.json(), status_code=response.status_code)


@cbv.cbv(router)
class VirtualFolderInfo:
    current_identity: dict = Depends(jwt_required)

    @router.delete(
        '/collections/{collection_id}',
        summary='delete collection',
    )
    async def delete(self, collection_id: str):
        _res = APIResponse()

        try:
            vfolder = get_collection_by_id(collection_id)

            if self.current_identity['role'] != 'admin':
                if vfolder['owner'] != self.current_identity['username']:
                    _res.set_code(EAPIResponseCode.bad_request)
                    _res.set_result('no permission for this project')
                    return _res.json_response()

            url = f'{ConfigClass.METADATA_SERVICE}collection/'
            params = {'id': collection_id}
            async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                response = await client.delete(url, params=params)
            if response.status_code != 200:
                logger.error(f'Failed to delete collection: {response.text}')
                _res.set_code(EAPIResponseCode.internal_error)
                _res.set_result('Failed to delete collection')
                return _res.json_response()
            else:
                logger.info(f'Successfully delete collection: {collection_id}')
                return response.json()
        except Exception as e:
            logger.error(f'errors in delete collection: {e}')
            _res.set_code(EAPIResponseCode.internal_error)
            _res.set_result('Failed to delete collection')
            return _res.json_response()
