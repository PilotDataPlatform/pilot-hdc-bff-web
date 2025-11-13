# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from collections.abc import Mapping
from typing import Annotated
from typing import ClassVar
from typing import Literal
from uuid import UUID
from uuid import uuid4

import fastapi
import httpx
import requests
from common import ProjectNotFoundException
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Header
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_utils import cbv
from pydantic import BaseModel
from starlette.datastructures import MultiDict

from app.auth import jwt_required
from app.components.exceptions import APIException
from app.components.exceptions import UnhandledException
from app.components.user.models import CurrentUser
from app.logger import logger
from config import ConfigClass
from models.api_response import EAPIResponseCode
from models.user_type import EUserRole
from services.dataset.client import DatasetServiceClient
from services.dataset.client import get_dataset_service_client
from services.permissions_service.decorators import DatasetPermission
from services.project.client import ProjectServiceClient
from services.project.client import get_project_service_client

router = APIRouter(tags=['Dataset'])


@cbv.cbv(router)
class Dataset:
    current_identity: CurrentUser = Depends(jwt_required)
    project_service_client: ProjectServiceClient = Depends(get_project_service_client)

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
            if not await self.current_identity.can_access_dataset(dataset, self.project_service_client):
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
    current_identity: CurrentUser = Depends(jwt_required)
    project_service_client: ProjectServiceClient = Depends(get_project_service_client)

    @router.post('/datasets/', summary='Create dataset')
    async def post(self, request: Request):
        payload_json = await request.json()

        dataset_code = payload_json.get('code', '').strip()
        if dataset_code in ConfigClass.FORBIDDEN_CONTAINER_CODES:
            raise APIException(error_msg='Dataset code is not allowed', status_code=EAPIResponseCode.forbidden.value)

        project_code = payload_json.pop('project_code', '').strip()
        if not self.current_identity.can_access_project(project_code):
            raise APIException(error_msg='Project code is not allowed', status_code=EAPIResponseCode.forbidden.value)

        project = await self.project_service_client.get(code=project_code)
        payload_json['project_id'] = project.id

        url = ConfigClass.DATASET_SERVICE + 'datasets/'
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


class ProxyPass:
    """PoC implementation of proxy pass.

    The goal is to generalize the method for defining a path to listen to, specifying allowed parameters, and
    determining which service should be called, all without the need to write a lot of duplicated code.
    """

    request_allowed_parameters: ClassVar[set[str]]

    response_allowed_headers: ClassVar[set[str]]

    async def __call__(self, request: Request) -> fastapi.Response:
        """Main method that will be called to process request into route."""

        filtered_parameters = await self.filter_request_parameters(request)
        parameters = await self.modify_request_parameters(filtered_parameters)
        raw_response = await self.proxy_request(parameters)
        response = await self.process_response(raw_response)

        return response

    async def filter_request_parameters(self, request: Request) -> MultiDict[str]:
        """Iterate over query parameters and keep only allowed."""

        parameters = MultiDict()

        for allowed_parameter in self.request_allowed_parameters:
            if allowed_parameter in request.query_params:
                for value in request.query_params.getlist(allowed_parameter):
                    parameters.append(allowed_parameter, value)

        return parameters

    async def modify_request_parameters(self, parameters: MultiDict[str]) -> MultiDict[str]:
        """Perform modification over the query parameters."""

        return MultiDict(parameters)

    async def proxy_request(self, parameters: MultiDict[str]) -> httpx.Response:
        """Perform request to the underlying service."""

        return httpx.Response(status_code=100)

    async def raise_for_response_status(self, response: httpx.Response) -> None:
        """Raise exception when received response is not successful."""

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError:
            logger.error(
                f'Received "{response.status_code}" status code in response when calling "{response.request.url}" url'
            )
            raise UnhandledException

    async def filter_response_headers(self, headers: httpx.Headers) -> Mapping[str, str]:
        """Iterate over response headers and keep only allowed."""

        processed_headers = {}

        for header in self.response_allowed_headers:
            if header in headers:
                processed_headers[header] = headers[header]

        return processed_headers

    async def process_response(self, response: httpx.Response) -> fastapi.Response:
        """Take the response from the underlying service and process it, so it can be returned to initial caller."""

        await self.raise_for_response_status(response)

        headers = await self.filter_response_headers(response.headers)

        return fastapi.Response(content=response.content, status_code=response.status_code, headers=headers)


@cbv.cbv(router)
class ListDatasets(ProxyPass):
    request_allowed_parameters: ClassVar[set[str]] = {
        'creator',
        'project_code',
        'sort_by',
        'sort_order',
        'page',
        'page_size',
    }
    response_allowed_headers: ClassVar[set[str]] = {'Content-Type'}

    current_user: CurrentUser = Depends(jwt_required)
    project_service_client: ProjectServiceClient = Depends(get_project_service_client)
    dataset_service_client: DatasetServiceClient = Depends(get_dataset_service_client)

    @router.get('/datasets/', summary='List all Datasets user can access.')
    async def __call__(self, request: Request) -> fastapi.Response:
        return await super().__call__(request)

    async def modify_request_parameters(self, parameters: MultiDict[str]) -> MultiDict[str]:
        """Replace parameters with appropriate for Dataset Service and check permissions.

        - If the creator parameter is specified it is set with the current username.
        - If the project_code parameter is specified it is part of projects to which the current user has access.
        - If neither creator nor project_code parameters are specified filtering by projects where user has admin roles
        or where user is the creator.
        """

        modified_parameters = MultiDict(parameters)

        creator_parameter = modified_parameters.pop('creator', None)
        project_code_parameter = modified_parameters.pop('project_code', None)

        user_projects_with_admin_role = self.current_user.get_projects_with_role('admin')

        if not creator_parameter and not project_code_parameter and user_projects_with_admin_role:
            project_ids = []
            for project_code in user_projects_with_admin_role:
                project = await self.project_service_client.get(code=project_code)
                project_ids.append(project.id)
            modified_parameters['project_id_any'] = ','.join(project_ids)
            modified_parameters['or_creator'] = self.current_user.username

            return modified_parameters

        if creator_parameter or not user_projects_with_admin_role:
            modified_parameters['creator'] = self.current_user.username

        if project_code_parameter:
            user_project_roles = self.current_user.get_project_roles()

            if project_code_parameter not in user_project_roles:
                raise APIException(error_msg='Permission denied', status_code=EAPIResponseCode.forbidden.value)

            project_role = user_project_roles[project_code_parameter]
            if project_role != EUserRole.admin.name:
                modified_parameters['creator'] = self.current_user.username

            project = await self.project_service_client.get(code=project_code_parameter)
            modified_parameters['project_id'] = project.id

        return modified_parameters

    async def proxy_request(self, parameters: MultiDict[str]) -> httpx.Response:
        return await self.dataset_service_client.list_datasets(parameters)


@cbv.cbv(router)
class ListDatasetVersionSharingRequests(ProxyPass):
    request_allowed_parameters: ClassVar[set[str]] = {
        'project_code',
        'sort_by',
        'sort_order',
        'page',
        'page_size',
    }
    response_allowed_headers: ClassVar[set[str]] = {'Content-Type'}

    current_user: CurrentUser = Depends(jwt_required)
    project_service_client: ProjectServiceClient = Depends(get_project_service_client)
    dataset_service_client: DatasetServiceClient = Depends(get_dataset_service_client)

    @router.get(
        '/dataset-version-sharing-requests/', summary='List all Dataset Version Sharing Requests user can access.'
    )
    async def __call__(self, request: Request) -> fastapi.Response:
        return await super().__call__(request)

    async def modify_request_parameters(self, parameters: MultiDict[str]) -> MultiDict[str]:
        modified_parameters = MultiDict(parameters)

        user_projects_with_admin_role = self.current_user.get_projects_with_role('admin')
        project_code_parameter = modified_parameters.get('project_code', None)
        if project_code_parameter not in user_projects_with_admin_role:
            raise APIException(error_msg='Permission denied', status_code=EAPIResponseCode.forbidden.value)

        return modified_parameters

    async def proxy_request(self, parameters: MultiDict[str]) -> httpx.Response:
        return await self.dataset_service_client.list_dataset_version_sharing_requests(parameters)

    async def process_response(self, response: httpx.Response) -> fastapi.Response:
        """Replace source project id with source project code in version sharing objects."""

        await self.raise_for_response_status(response)

        headers = await self.filter_response_headers(response.headers)

        content = response.json()
        for version_sharing_request in content['result']:
            source_project = await self.project_service_client.get(id=version_sharing_request.pop('source_project_id'))
            version_sharing_request['source_project_code'] = source_project.code

        return JSONResponse(content=content, status_code=response.status_code, headers=headers)


class CreateDatasetVersionSharingRequestBody(BaseModel):
    version_id: UUID
    project_code: str


class UpdateDatasetVersionSharingRequestBody(BaseModel):
    status: Literal['accepted', 'declined']


@cbv.cbv(router)
class DatasetVersionSharingRequest(ProxyPass):
    response_allowed_headers: ClassVar[set[str]] = {'Content-Type'}

    current_user: CurrentUser = Depends(jwt_required)
    project_service_client: ProjectServiceClient = Depends(get_project_service_client)
    dataset_service_client: DatasetServiceClient = Depends(get_dataset_service_client)

    @router.post('/dataset-version-sharing-requests/', summary='Create Dataset Version Sharing Request')
    async def post(self, body: CreateDatasetVersionSharingRequestBody) -> fastapi.Response:
        try:
            project = await self.project_service_client.get(code=body.project_code)
            dataset_version = await self.dataset_service_client.get_dataset_version(body.version_id)
            dataset = await self.dataset_service_client.get_dataset_by_id(dataset_version['dataset_id'])
            dataset_source_project = await self.project_service_client.get(id=dataset['project_id'])
        except ProjectNotFoundException:
            raise APIException(error_msg='Project not found', status_code=EAPIResponseCode.not_found.value)

        if dataset['project_id'] == project.id:
            raise APIException(
                error_msg='Sharing is not permitted within the same project',
                status_code=EAPIResponseCode.conflict.value,
            )

        user_projects_with_admin_role = self.current_user.get_projects_with_role('admin')
        if dataset_source_project.code not in user_projects_with_admin_role:
            raise APIException(error_msg='Permission denied', status_code=EAPIResponseCode.forbidden.value)

        raw_response = await self.dataset_service_client.create_dataset_version_sharing_request(
            body.version_id, project.code, self.current_user.username
        )
        response = await self.process_response(raw_response)

        return response

    @router.patch(
        '/dataset-version-sharing-requests/{version_sharing_request_id}',
        summary='Update Dataset Version Sharing Request',
    )
    async def patch(
        self,
        version_sharing_request_id: UUID,
        body: UpdateDatasetVersionSharingRequestBody,
        session_id: Annotated[str | None, Header()] = None,
        authorization: Annotated[str | None, Header()] = None,
    ):
        response = await self.dataset_service_client.get_dataset_version_sharing_request(version_sharing_request_id)
        response.raise_for_status()
        existing_version_sharing_request = response.json()

        if existing_version_sharing_request['status'] in ('accepted', 'declined'):
            raise APIException(error_msg='Version sharing request is already processed', status_code=400)

        user_projects_with_admin_role = self.current_user.get_projects_with_role('admin')
        if existing_version_sharing_request['project_code'] not in user_projects_with_admin_role:
            raise APIException(error_msg='Permission denied', status_code=EAPIResponseCode.forbidden.value)

        is_accepted = body.status == 'accepted'

        if is_accepted and (session_id is None or authorization is None):
            raise APIException(error_msg='Missing required headers.', status_code=EAPIResponseCode.forbidden.value)

        raw_response = await self.dataset_service_client.process_dataset_version_sharing_request(
            version_sharing_request_id, self.current_user.username, body.status
        )
        await self.raise_for_response_status(raw_response)
        version_sharing_request = raw_response.json()
        source_project = await self.project_service_client.get(id=version_sharing_request.pop('source_project_id'))
        version_sharing_request['source_project_code'] = source_project.code

        if is_accepted:
            job_id = str(uuid4())
            response = await self.dataset_service_client.start_version_sharing_request(
                version_sharing_request_id, job_id, session_id, authorization
            )
            response.raise_for_status()
            logger.info(
                f'Successfully started sharing a version sharing request "{version_sharing_request_id}" '
                f'using job "{job_id}" in session "{session_id}".'
            )

        return JSONResponse(content=version_sharing_request, status_code=raw_response.status_code)


@cbv.cbv(router)
class DatasetFiles:
    current_identity: CurrentUser = Depends(jwt_required)

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
    current_identity: CurrentUser = Depends(jwt_required)

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
    current_identity: CurrentUser = Depends(jwt_required)
    dataset_service_client: DatasetServiceClient = Depends(get_dataset_service_client)

    @router.get(
        '/dataset/{dataset_id}/file/tasks',
        summary='Dataset Tasks',
        dependencies=[Depends(DatasetPermission())],
    )
    async def get(self, dataset_id: str, request: Request):
        request_params = request.query_params
        new_params = {**request_params, 'label': 'Dataset'}

        dataset = await self.dataset_service_client.get_dataset_by_id(dataset_id)
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

        dataset = await self.dataset_service_client.get_dataset_by_id(dataset_id)
        request_body['code'] = dataset['code']

        url = ConfigClass.DATAOPS_SERVICE + 'tasks'
        response = requests.delete(url, json=request_body, timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT)
        return JSONResponse(content=response.json(), status_code=response.status_code)
