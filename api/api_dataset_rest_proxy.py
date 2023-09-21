# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import httpx
import requests
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_utils import cbv

from app.auth import jwt_required
from app.components.exceptions import APIException
from config import ConfigClass
from models.api_response import EAPIResponseCode
from services.dataset import get_dataset_by_id
from services.permissions_service.decorators import DatasetPermission

router = APIRouter(tags=['Dataset'])


@cbv.cbv(router)
class Dataset:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/datasets/{dataset_id_or_code}',
        summary='Get dataset by id or code',
    )
    async def get(self, dataset_id_or_code: str):
        url = f'{ConfigClass.DATASET_SERVICE}datasets/{dataset_id_or_code}'
        async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
            response = await client.get(url)
        if response.status_code == 200:
            dataset = response.json()
            if dataset['creator'] != self.current_identity['username']:
                raise APIException(error_msg='Permission denied', status_code=EAPIResponseCode.forbidden.value)
        return JSONResponse(content=response.json(), status_code=response.status_code)

    @router.put('/datasets/{dataset_id}', summary='Update dataset by id', dependencies=[Depends(DatasetPermission())])
    async def put(self, dataset_id: str, request: Request):
        url = f'{ConfigClass.DATASET_SERVICE}datasets/{dataset_id}'
        payload_json = await request.json()
        respon = requests.put(
            url, json=payload_json, headers=request.headers, timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT
        )
        return JSONResponse(content=respon.json(), status_code=respon.status_code)


@cbv.cbv(router)
class RestfulPost:
    current_identity: dict = Depends(jwt_required)

    @router.post(
        '/datasets/',
        summary='create dataset',
    )
    async def post(self, request: Request):
        url = ConfigClass.DATASET_SERVICE + 'datasets/'
        payload_json = await request.json()
        operator_username = self.current_identity['username']
        dataset_creator = payload_json.get('creator')
        if operator_username != dataset_creator:
            return JSONResponse(
                content={'err_msg': f'No permissions: {operator_username} cannot create dataset for {dataset_creator}'},
                status_code=403,
            )
        async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
            headers = dict(request.headers)
            del headers['content-length']
            respon = await client.post(url, json=payload_json, headers=headers)

        return JSONResponse(content=respon.json(), status_code=respon.status_code)


@cbv.cbv(router)
class List:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/datasets/',
        summary='List users datasets',
    )
    async def get(self, request: Request):
        url = ConfigClass.DATASET_SERVICE + 'datasets/'
        username = request.query_params.get('creator')
        operator_username = self.current_identity['username']
        if operator_username != username:
            return JSONResponse(content={'err_msg': 'No permissions'}, status_code=403)
        async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
            respon = await client.get(url, params=dict(request.query_params))
        return JSONResponse(content=respon.json(), status_code=respon.status_code)


@cbv.cbv(router)
class DatasetFiles:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/dataset/{dataset_id}/files',
        summary='List dataset files',
        dependencies=[Depends(DatasetPermission())],
    )
    def get(self, dataset_id: str, request: Request):
        url = f'{ConfigClass.DATASET_SERVICE}dataset/{dataset_id}/files'
        response = requests.get(
            url, params=request.query_params, headers=request.headers, timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT
        )
        if response.status_code != 200:
            return response.json(), response.status_code
        entities = []
        for file_node in response.json()['result']['data']:
            file_node['zone'] = 'greenroom' if file_node['zone'] == 0 else 'core'
            entities.append(file_node)
        result = response.json()
        result['result']['data'] = entities
        return JSONResponse(content=result, status_code=response.status_code)

    @router.post(
        '/dataset/{dataset_id}/files',
        summary='Move dataset files',
        dependencies=[Depends(DatasetPermission())],
    )
    async def post(self, dataset_id: str, request: Request):
        url = f'{ConfigClass.DATASET_SERVICE}dataset/{dataset_id}/files'
        payload_json = await request.json()
        respon = requests.post(
            url, json=payload_json, headers=request.headers, timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT
        )
        return JSONResponse(content=respon.json(), status_code=respon.status_code)

    @router.put(
        '/dataset/{dataset_id}/files',
        summary='Recieve the file list from a project and Copy them under the dataset',
        dependencies=[Depends(DatasetPermission())],
    )
    async def put(self, dataset_id: str, request: Request):
        url = f'{ConfigClass.DATASET_SERVICE}dataset/{dataset_id}/files'
        payload_json = await request.json()
        respon = requests.put(
            url, json=payload_json, headers=request.headers, timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT
        )
        return JSONResponse(content=respon.json(), status_code=respon.status_code)

    @router.delete(
        '/dataset/{dataset_id}/files',
        summary='Remove dataset files',
        dependencies=[Depends(DatasetPermission())],
    )
    async def delete(self, dataset_id: str, request: Request):
        url = f'{ConfigClass.DATASET_SERVICE}dataset/{dataset_id}/files'
        payload_json = await request.json()
        respon = requests.delete(
            url, json=payload_json, headers=request.headers, timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT
        )
        return JSONResponse(content=respon.json(), status_code=respon.status_code)


@cbv.cbv(router)
class DatasetFileUpdate:
    current_identity: dict = Depends(jwt_required)

    @router.post(
        '/dataset/{dataset_id}/files/{file_id}',
        summary='update files within the dataset',
        dependencies=[Depends(DatasetPermission())],
    )
    async def post(self, dataset_id: str, file_id: str, request: Request):
        url = f'{ConfigClass.DATASET_SERVICE}dataset/{dataset_id}/files/{file_id}'
        payload_json = await request.json()
        respon = requests.post(
            url, json=payload_json, headers=request.headers, timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT
        )
        return JSONResponse(content=respon.json(), status_code=respon.status_code)


@cbv.cbv(router)
class DatsetTasks:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/dataset/{dataset_id}/file/tasks',
        summary='Dataset Tasks',
        dependencies=[Depends(DatasetPermission())],
    )
    async def get(self, dataset_id: str, request: Request):
        request_params = request.query_params
        new_params = {**request_params, 'label': 'Dataset'}

        dataset = await get_dataset_by_id(dataset_id)
        new_params['code'] = dataset['code']

        url = ConfigClass.DATAOPS_SERVICE + 'tasks'
        response = requests.get(url, params=new_params, timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT)
        return JSONResponse(content=response.json(), status_code=response.status_code)

    @router.delete(
        '/dataset/{dataset_id}/file/tasks',
        summary='Dataset Tasks',
        dependencies=[Depends(DatasetPermission())],
    )
    async def delete(self, dataset_id: str, request: Request):
        request_body = await request.json()
        request_body.update({'label': 'Dataset'})

        dataset = await get_dataset_by_id(dataset_id)
        request_body['code'] = dataset['code']

        url = ConfigClass.DATAOPS_SERVICE + 'tasks'
        response = requests.delete(url, json=request_body, timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT)
        return JSONResponse(content=response.json(), status_code=response.status_code)
