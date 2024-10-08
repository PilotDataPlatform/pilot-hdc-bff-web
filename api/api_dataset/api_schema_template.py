# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import requests
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_utils import cbv

from app.auth import jwt_required
from app.components.user.models import CurrentUser
from config import ConfigClass
from services.permissions_service.decorators import DatasetPermission

router = APIRouter(tags=['Dataset Schema Template'])


@cbv.cbv(router)
class SchemaTemplate:
    current_identity: CurrentUser = Depends(jwt_required)

    @router.get(
        '/dataset/{dataset_id}/schemaTPL/{template_id}',
        summary='Get schema template by id',
        dependencies=[Depends(DatasetPermission())],
    )
    async def get(self, dataset_id: str, template_id: str, request: Request):
        url = ConfigClass.DATASET_SERVICE + f'dataset/{dataset_id}/schemaTPL/{template_id}'
        respon = requests.get(
            url, params=request.query_params, headers=request.headers, timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT
        )
        return JSONResponse(content=respon.json(), status_code=respon.status_code)

    @router.put(
        '/dataset/{dataset_id}/schemaTPL/{template_id}',
        summary='Update schema template by id',
        dependencies=[Depends(DatasetPermission())],
    )
    async def put(self, dataset_id: str, template_id: str, request: Request):
        url = ConfigClass.DATASET_SERVICE + f'dataset/{dataset_id}/schemaTPL/{template_id}'
        payload_json = await request.json()
        respon = requests.put(
            url, json=payload_json, headers=request.headers, timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT
        )
        return JSONResponse(content=respon.json(), status_code=respon.status_code)

    @router.delete(
        '/dataset/{dataset_id}/schemaTPL/{template_id}',
        summary='Delete schema template by id',
        dependencies=[Depends(DatasetPermission())],
    )
    async def delete(self, dataset_id: str, template_id: str, request: Request):
        url = ConfigClass.DATASET_SERVICE + f'dataset/{dataset_id}/schemaTPL/{template_id}'
        payload_json = await request.json()
        respon = requests.delete(
            url, json=payload_json, headers=request.headers, timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT
        )
        return JSONResponse(content=respon.json(), status_code=respon.status_code)


@cbv.cbv(router)
class SchemaTemplateCreate:
    current_identity: CurrentUser = Depends(jwt_required)

    @router.post(
        '/dataset/{dataset_id}/schemaTPL',
        summary='Create schema template',
        dependencies=[Depends(DatasetPermission())],
    )
    async def post(self, dataset_id: str, request: Request):
        url = ConfigClass.DATASET_SERVICE + f'dataset/{dataset_id}/schemaTPL'
        payload_json = await request.json()
        respon = requests.post(
            url, json=payload_json, headers=request.headers, timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT
        )
        return JSONResponse(content=respon.json(), status_code=respon.status_code)


@cbv.cbv(router)
class SchemaTemplatePostQuery:
    @router.post(
        '/dataset/{dataset_id}/schemaTPL/list',
        summary='List and query schema templates',
        dependencies=[Depends(DatasetPermission())],
    )
    async def post(self, dataset_id: str, request: Request):
        url = ConfigClass.DATASET_SERVICE + f'dataset/{dataset_id}/schemaTPL/list'
        payload_json = await request.json()
        respon = requests.post(
            url, json=payload_json, headers=request.headers, timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT
        )
        return JSONResponse(content=respon.json(), status_code=respon.status_code)


@cbv.cbv(router)
class SchemaTemplateDefaultQuery:
    @router.post(
        '/dataset/schemaTPL/list',
        summary='List and query schema templates',
    )
    async def post(self, request: Request):
        url = ConfigClass.DATASET_SERVICE + 'dataset/default/schemaTPL/list'
        payload_json = await request.json()
        respon = requests.post(
            url, json=payload_json, headers=request.headers, timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT
        )
        return JSONResponse(content=respon.json(), status_code=respon.status_code)


@cbv.cbv(router)
class SchemaTemplateDefaultGet:
    @router.get(
        '/dataset/schemaTPL/default/{template_id}',
        summary='Get default schema',
    )
    async def get(self, template_id: str, request: Request):
        url = ConfigClass.DATASET_SERVICE + f'dataset/default/schemaTPL/{template_id}'
        respon = requests.get(
            url, params=request.query_params, headers=request.headers, timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT
        )
        return JSONResponse(content=respon.json(), status_code=respon.status_code)
