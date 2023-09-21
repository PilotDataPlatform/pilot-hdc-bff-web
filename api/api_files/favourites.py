# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import httpx
import requests
from common import has_file_permission
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from fastapi_utils import cbv

from app.auth import jwt_required
from app.components.exceptions import APIException
from config import ConfigClass
from models.api_response import EAPIResponseCode
from services.meta import get_entity_by_id

router = APIRouter(tags=['Favourites'])


@cbv.cbv(router)
class Favourites:
    current_identity: dict = Depends(jwt_required)

    @router.get('/favourites', summary='Get all favourites for a user')
    async def get_user_favourites(self, request: Request):
        user = self.current_identity['username']
        params = {
            'page_size': int(request.query_params.get('page_size', 25)),
            'page': int(request.query_params.get('page', 0)),
            'order': request.query_params.get('order', 'desc'),
            'sorting': request.query_params.get('sorting', 'created_time'),
        }
        async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
            response = await client.get(f'{ConfigClass.METADATA_SERVICE}favourites/{user}/', params=params)
        return JSONResponse(content=response.json(), status_code=response.status_code)

    @router.post('/favourite', summary='Favourite an entity')
    async def create_favourite(self, request: Request):
        payload = await request.json()
        payload['zone'] = ConfigClass.LABEL_ZONE_MAPPING[payload['zone'].lower()]
        if payload['type'] == 'item':
            file_node = await run_in_threadpool(get_entity_by_id, payload['id'])
            if not await has_file_permission(ConfigClass.AUTH_SERVICE, file_node, 'view', self.current_identity):
                raise APIException(error_msg='Permission denied', status_code=EAPIResponseCode.forbidden.value)
        payload['user'] = self.current_identity['username']
        async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
            response = await client.post(f'{ConfigClass.METADATA_SERVICE}favourite/', json=payload)
        return JSONResponse(content=response.json(), status_code=response.status_code)

    @router.delete('/favourite', summary='Remove an existing favourite')
    async def delete_favourite(self, id_: str = Query(alias='id'), type_: str = Query(alias='type')):
        params = {'id': id_, 'user': self.current_identity['username'], 'type': type_}
        async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
            response = await client.delete(f'{ConfigClass.METADATA_SERVICE}favourite/', params=params)
        return JSONResponse(content=response.json(), status_code=response.status_code)

    @router.delete('/favourites', summary='Remove many existing favourites')
    async def delete_favourites(self, request: Request):
        params = {'user': self.current_identity['username']}
        payload = await request.json()
        response = requests.delete(
            f'{ConfigClass.METADATA_SERVICE}favourites/',
            params=params,
            json=payload,
            timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT,
        )
        return JSONResponse(content=response.json(), status_code=response.status_code)

    @router.patch('/favourite', summary='Pin or unpin an existing favourite')
    async def pin_unpin_favourite(
        self,
        pinned: bool,
        id_: str = Query(alias='id'),
        type_: str = Query(alias='type'),
    ):
        params = {
            'id': id_,
            'user': self.current_identity['username'],
            'type': type_,
            'pinned': pinned,
        }
        async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
            response = await client.patch(f'{ConfigClass.METADATA_SERVICE}favourite/', params=params)
        return JSONResponse(content=response.json(), status_code=response.status_code)

    @router.patch('/favourites', summary='Pin or unpin many existing favourites')
    async def pin_unpin_favourites(self, request: Request):
        params = {'user': self.current_identity['username']}
        payload = await request.json()
        async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
            response = await client.patch(f'{ConfigClass.METADATA_SERVICE}favourites/', params=params, json=payload)
        return JSONResponse(content=response.json(), status_code=response.status_code)
