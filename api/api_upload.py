# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import httpx
from common import has_file_permission
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.concurrency import run_in_threadpool
from fastapi_utils.cbv import cbv

from app.auth import jwt_required
from app.components.exceptions import APIException
from app.components.user.models import CurrentUser
from app.logger import logger
from config import ConfigClass
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode
from models.api_upload import POSTProjectFile
from models.api_upload import ResumableResponse
from models.api_upload import ResumableUploadPOST
from models.models_item import ItemStatus
from services.meta import get_entity_by_id

router = APIRouter()
_API_NAMESPACE = 'api_upload'


@cbv(router)
class APIProject:
    current_identity: CurrentUser = Depends(jwt_required)

    @router.post(
        '/project/{project_code}/files',
        summary='proxy to upload service to pre upload file to the target zone',
        tags=['V1 Files'],
    )
    async def project_file_preupload(
        self,
        project_code,
        request: Request,
        data: POSTProjectFile,
    ):
        """PRE upload and check existence of file in project."""
        api_response = APIResponse()
        logger.info('API project_file_preupload'.center(80, '-'))

        parent_folder = await run_in_threadpool(get_entity_by_id, data.parent_folder_id)
        if not await has_file_permission(ConfigClass.AUTH_SERVICE, parent_folder, 'upload', self.current_identity):
            raise APIException(
                error_msg='Permission Denied',
                status_code=EAPIResponseCode.forbidden.value,
            )
        if len(data.folder_tags) > 0 and not await has_file_permission(
            ConfigClass.AUTH_SERVICE, parent_folder, 'annotate', self.current_identity
        ):
            raise APIException(
                error_msg='Permission Denied',
                status_code=EAPIResponseCode.forbidden.value,
            )

        try:
            logger.info('Tansfering to pre upload')
            payload = {
                'current_folder_node': data.current_folder_node,
                'parent_folder_id': data.parent_folder_id,
                'project_code': project_code,
                'operator': data.operator,
                'data': data.data,
                'job_type': data.job_type,
            }

            url = ConfigClass.UPLOAD_SERVICE + '/v1/files/jobs'
            headers = {
                'Authorization': request.headers.get('Authorization'),
                'Session-ID': request.headers.get('Session-ID', ''),
            }
            async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                result = await client.post(url, headers=headers, json=payload, timeout=None)
                logger.info(f'pre response: {result.text}')

            if result.status_code == 409:
                api_response.set_error_msg(result.json()['error_msg'])
                api_response.set_code(EAPIResponseCode.conflict)
            elif result.status_code != 200:
                api_response.set_error_msg('Upload Error: ' + result.text)
                api_response.set_code(EAPIResponseCode.internal_error)
            else:
                api_response.set_result(result.json()['result'])

            return api_response.json_response()
        except Exception as e:
            error_msg = f'Preupload error: {e}'
            logger.error(error_msg)
            api_response.set_error_msg(error_msg)
            api_response.set_code(EAPIResponseCode.internal_error)

            return api_response.json_response()

    @router.get(
        '/project/{project_code}/files/chunks/presigned',
        summary='proxy to upload service to generate presigned chunk url',
        tags=['V1 Files'],
    )
    async def generate_presigned_url_chunks(
        self, project_code, request: Request, key: str, upload_id: str, chunk_number: int
    ):
        """
        Summary:
            The api will proxy to upload service and generate presigned url
            for chunk uploading chunks
            Path Parameter:
                - project_code(str): unique identifier of project
            Parameter:
                - key(str): file path
                - upload_id(str): the unique identifier of upload process
                - chunk_number(int): the number of chunk
        return:
            - result(str): presigned url
        """
        api_response = APIResponse()
        logger.info('API project_file_preupload'.center(80, '-'))

        try:
            logger.info('Generate presigned url for chunks')
            params = {
                'bucket': 'gr-' + project_code,
                'key': key,
                'upload_id': upload_id,
                'chunk_number': chunk_number,
            }
            headers = {'Session-ID': request.headers.get('Session-ID', '')}
            url = ConfigClass.UPLOAD_SERVICE + '/v1/files/chunks/presigned'
            async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                result = await client.get(url, headers=headers, params=params, timeout=None)
                logger.info(f'chunk presigned response: {result.text}')

            if result.status_code != 200:
                api_response.set_error_msg('chunk presigned Error: ' + result.text)
                api_response.set_code(EAPIResponseCode.internal_error)
            else:
                api_response.set_result(result.json()['result'])

            return api_response.json_response()
        except Exception as e:
            error_msg = f'get presigned error: {e}'
            logger.error(error_msg)
            api_response.set_error_msg(error_msg)
            api_response.set_code(EAPIResponseCode.internal_error)

            return api_response.json_response()

    @router.post(
        '/project/{project_code}/files/resumable',
        response_model=ResumableResponse,
        summary='resumable upload check',
        tags=['V1 Files'],
    )
    async def project_file_resumable(
        self,
        project_code,
        request: Request,
        data: ResumableUploadPOST,
    ):
        """
        Summary:
            the api to check the uploaded chunk in the object
            storage. Afterwards, client will resume the previous
            upload.
        Payload:
            - object_infos(List[ObjectInfo]): the list of pairs contains following:
                - object_path(str): the unique path in object storage
                - resumable_id(str): the unique identifier for resumable upload
        return:
            - result(list):
                - object_path(str): the unique path in object storage
                - resumable_id(str): the unique identifier for resumable upload
                - chunks_info(dict[str: str]): the pair of chunk_number: etag
        """
        api_response = APIResponse()
        headers = {
            'Authorization': request.headers.get('Authorization'),
        }
        for x in data.object_infos:
            item = await run_in_threadpool(get_entity_by_id, x.item_id)
            if not await has_file_permission(ConfigClass.AUTH_SERVICE, item, 'upload', self.current_identity):
                raise APIException(
                    error_msg='Permission Denied',
                    status_code=EAPIResponseCode.forbidden.value,
                )

        try:
            async with httpx.AsyncClient() as client:
                url = ConfigClass.UPLOAD_SERVICE + '/v1/files/resumable'
                object_infos = [dict(x) for x in data.object_infos]
                payload = {'bucket': 'gr-' + project_code, 'object_infos': object_infos}
                res = await client.post(url, headers=headers, json=payload, timeout=None)
                api_response.set_result(res.json().get('result', []))

            return api_response.json_response()
        except Exception as e:
            error_msg = f'get resumable error: {e}'
            logger.error(error_msg)
            api_response.set_error_msg(error_msg)
            api_response.set_code(EAPIResponseCode.internal_error)

            return api_response.json_response()

    @router.get(
        '/project/{project_code}/files/resumable',
        summary='list all registered file of specific user',
        tags=['V1 Files'],
    )
    async def project_file_resumable_list(self, project_code, request: Request):
        """
        Summary:
            the api to list ALL registered file in the database. The registered
            file means the upload process is not finished(either in progress or stop
            in middle)
        Parameter:
            - project_code: the unique identifier of project
        return:
            - result(list of item entity)
        """
        api_response = APIResponse()
        try:
            async with httpx.AsyncClient() as client:
                url = ConfigClass.METADATA_SERVICE + 'items/search/'
                params = {
                    'container_code': project_code,
                    'container_type': 'project',
                    'owner': self.current_identity.get('username'),
                    'zone': 0,
                    'recursive': True,
                    'status': ItemStatus.REGISTERED,
                    'page_size': 1000,
                    'sorting': 'last_updated_time',
                    'order': 'desc',
                }
                headers = {'Authorization': request.headers.get('Authorization')}
                res = await client.get(url, params=params, headers=headers, timeout=None)

                api_response.set_code(res.status_code)
                if res.status_code == 200:
                    api_response.set_result(res.json().get('result', []))

            return api_response.json_response()
        except Exception as e:
            error_msg = f'list resumable error: {e}'
            logger.error(error_msg)
            api_response.set_error_msg(error_msg)
            api_response.set_code(EAPIResponseCode.internal_error)

            return api_response.json_response()


async def search_file_permissions_check(project_code, parent_path, name, headers, status=ItemStatus.ACTIVE):
    async with httpx.AsyncClient() as client:
        url = ConfigClass.METADATA_SERVICE + 'items/search/'
        params = {
            'container_code': project_code,
            'container_type': 'project',
            'zone': 0,
            'name': name,
            'status': status,
            'parent_path': parent_path,
        }
        res = await client.get(url, params=params, headers=headers, timeout=None)
    if res.status_code != 200:
        error_msg = f'error when get item: {res.content}'
        raise APIException(
            error_msg=error_msg,
            status_code=EAPIResponseCode.internal_error.value,
        )
    if not res.json().get('result'):
        raise APIException(
            error_msg='Permission Denied',
            status_code=EAPIResponseCode.forbidden.value,
        )
