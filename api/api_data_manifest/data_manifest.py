# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import httpx
from common import has_file_permission
from common import has_permission
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_utils import cbv

from app.auth import jwt_required
from app.components.exceptions import APIException
from app.logger import logger
from config import ConfigClass
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode
from models.models_item import ItemStatus
from services.meta import async_get_entity_by_id
from services.permissions_service.decorators import PermissionsCheck

router = APIRouter(tags=['Attribute Templates'])


@cbv.cbv(router)
class RestfulManifests:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/data/manifests',
        summary='List attribute templates by project_code',
    )
    async def get(self, request: Request):
        """List attribute templates by project_code."""
        try:
            async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                url = f'{ConfigClass.METADATA_SERVICE}template/'
                response = await client.get(url, params=request.query_params)

            return JSONResponse(content=response.json(), status_code=response.status_code)
        except Exception as e:
            logger.error(f'Error when calling metadata service: {e}')
            error_msg = {'result': str(e)}
            return JSONResponse(content=error_msg, status_code=500)

    @router.post(
        '/data/manifests',
        summary='Create a new attribute template',
        dependencies=[Depends(PermissionsCheck('file_attribute_template', '*', 'manage'))],
    )
    async def post(self, request: Request):
        """Create a new attribute template."""
        try:
            async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                url = f'{ConfigClass.METADATA_SERVICE}template/'
                response = await client.post(url, json=await request.json())

            return JSONResponse(content=response.json(), status_code=response.status_code)
        except Exception as e:
            logger.error(f'Error when calling metadata service: {e}')
            error_msg = {'result': str(e)}
            return JSONResponse(content=error_msg, status_code=500)


@cbv.cbv(router)
class RestfulManifest:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/data/manifest/{manifest_id}',
        summary='Get attribute template by id',
    )
    async def get(self, manifest_id: str):
        """Get an attribute template by id."""
        my_res = APIResponse()
        try:
            async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                url = f'{ConfigClass.METADATA_SERVICE}template/{manifest_id}/'
                response = await client.get(url)

            res = response.json()
            if not res['result']:
                my_res.set_code(EAPIResponseCode.not_found)
                my_res.set_error_msg('Attribute template not found')
                return my_res.json_response()

            for attr in res['result']['attributes']:
                attr['manifest_id'] = res['result']['id']
            return JSONResponse(content=res, status_code=response.status_code)
        except Exception as e:
            logger.error(f'Error when calling metadata service: {e}')
            error_msg = {'result': str(e)}
            return JSONResponse(content=error_msg, status_code=EAPIResponseCode.internal_error.value)

    @router.put(
        '/data/manifest/{manifest_id}',
        summary='Update attributes or name of a template by id',
        dependencies=[Depends(PermissionsCheck('file_attribute_template', '*', 'manage'))],
    )
    async def put(self, manifest_id: str, request: Request):
        """Update attributes or name of template by id."""
        my_res = APIResponse()
        data = await request.json()

        try:
            async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                url = f'{ConfigClass.METADATA_SERVICE}template/{manifest_id}/'
                response = await client.get(url)

            template = response.json()['result']
            if not template:
                my_res.set_code(EAPIResponseCode.not_found)
                my_res.set_error_msg('Attribute template not found')
                return my_res.json_response()

            if 'attributes' not in data:
                result = {'id': template['id'], 'name': template['name'], 'project_code': template['project_code']}
                data['attributes'] = template['attributes']
            else:
                result = ''
                existing_attr = template['attributes']
                data['attributes'] = data['attributes'] + existing_attr

            params = {'id': manifest_id}
            async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                url = f'{ConfigClass.METADATA_SERVICE}template/'
                response = await client.put(url, params=params, json=data)

            res = response.json()
            res['result'] = result
            return JSONResponse(content=res, status_code=response.status_code)
        except Exception as e:
            logger.error(f'Error when calling metadata service: {e}')
            error_msg = {'result': str(e)}
            return JSONResponse(content=error_msg, status_code=EAPIResponseCode.internal_error.value)

    @router.delete(
        '/data/manifest/{manifest_id}',
        summary='Delete an attribute template',
    )
    async def delete(self, manifest_id: str, request: Request):  # noqa: C901
        """Delete an attribute template."""
        my_res = APIResponse()
        async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
            url = f'{ConfigClass.METADATA_SERVICE}template/{manifest_id}/'
            response = await client.get(url)

        res = response.json()['result']
        if not res:
            my_res.set_code(EAPIResponseCode.not_found)
            my_res.set_error_msg('Attribute template not found')
            return my_res.json_response()

        project_code = res['project_code']
        if not await has_permission(
            ConfigClass.AUTH_SERVICE, project_code, 'file_attribute_template', '*', 'manage', self.current_identity
        ):
            my_res.set_code(EAPIResponseCode.forbidden)
            my_res.set_result('Permission denied')
            return my_res.json_response()

        try:
            for zone in [0, 1]:
                for status in [ItemStatus.ACTIVE, ItemStatus.ARCHIVED]:
                    params = {
                        'container_code': project_code,
                        'zone': zone,
                        'recursive': True,
                        'status': status,
                        'type': 'file',
                    }

                    async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                        auth = {'Authorization': request.headers.get('Authorization')}
                        url = f'{ConfigClass.METADATA_SERVICE}items/search/'
                        response = await client.get(url, params=params, headers=auth)

                    if response.status_code != 200:
                        my_res.set_code(EAPIResponseCode.internal_error)
                        my_res.set_error_msg('Failed to search for items')
                        return my_res.json_response()

                    items = response.json()['result']
                    for item in items:
                        if manifest_id in item['extended']['extra']['attributes']:
                            my_res.set_code(EAPIResponseCode.forbidden)
                            my_res.set_result('Cant delete manifest attached to files')
                            return my_res.json_response()

            params = {'id': manifest_id}

            async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                url = f'{ConfigClass.METADATA_SERVICE}template/'
                response = await client.delete(url, params=params)

            if response.status_code != 200:
                my_res.set_code(EAPIResponseCode.internal_error)
                my_res.set_error_msg('Failed to delete attribute template not found')
                return my_res.json_response()

            my_res.set_code(EAPIResponseCode.success)
            my_res.set_result('success')
            return my_res.json_response()
        except Exception as e:
            logger.error(f'Error when calling metadata service: {e}')
            error_msg = {'result': str(e)}
            return JSONResponse(content=error_msg, status_code=EAPIResponseCode.internal_error.value)


@cbv.cbv(router)
class FileAttributes:
    current_identity: dict = Depends(jwt_required)
    """Update attributes of template attached to a file."""

    @router.put(
        '/file/{file_id}/manifest',
        summary='Update attributes of template attached to a file',
    )
    async def put(self, file_id: str, request: Request):
        api_response = APIResponse()
        entity = await async_get_entity_by_id(file_id)
        if not entity['extended']['extra'].get('attributes'):
            raise APIException(
                status_code=EAPIResponseCode.bad_request.value, error_msg="File doesn't have an attached template"
            )
        template_id = list(entity['extended']['extra']['attributes'].keys())[0]
        zone = 'greenroom' if entity['zone'] == 0 else 'core'
        if not await has_file_permission(ConfigClass.AUTH_SERVICE, entity, 'annotate', self.current_identity):
            api_response.set_code(EAPIResponseCode.forbidden)
            api_response.set_result('Permission denied')
            return api_response.json_response()

        try:
            params = {'id': entity['id']}
            attributes_update = await request.json()
            payload = {
                'parent': entity['parent'],
                'parent_path': entity['parent_path'],
                'type': 'file',
                'tags': entity['extended']['extra']['tags'],
                'system_tags': entity['extended']['extra']['system_tags'],
                'attribute_template_id': template_id,
                'attributes': attributes_update,
            }
            async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                url = f'{ConfigClass.METADATA_SERVICE}item/'
                response = await client.put(url, params=params, json=payload)

            res = response.json()
            res['result']['zone'] = zone
            res['result'].pop('extended')
            res['result']['manifest_id'] = template_id
            res['result'] = {**res['result'], **{f'attr_{attr}': attributes_update[attr] for attr in attributes_update}}

            return JSONResponse(content=res, status_code=response.status_code)
        except Exception as e:
            logger.error(f'Error when calling metadata service: {e}')
            error_msg = {'result': str(e)}
            return JSONResponse(content=error_msg, status_code=EAPIResponseCode.internal_error.value)


@cbv.cbv(router)
class ImportManifest:
    current_identity: dict = Depends(jwt_required)
    """Import attribute template from portal as JSON."""

    @router.post(
        '/import/manifest',
        summary='Import attribute template from portal as JSON',
        dependencies=[Depends(PermissionsCheck('file_attribute_template', '*', 'manage'))],
    )
    async def post(self, request: Request):
        data = await request.json()
        try:

            payload = {'name': data['name'], 'project_code': data['project_code'], 'attributes': data['attributes']}
            async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                url = f'{ConfigClass.METADATA_SERVICE}template/'
                response = await client.post(url, json=payload)

            res = response.json()
            res['result'] = 'Success'
            return JSONResponse(content=res, status_code=response.status_code)
        except Exception as e:
            logger.error(f'Error when calling metadata service: {e}')
            error_msg = {'result': str(e)}
            return JSONResponse(content=error_msg, status_code=EAPIResponseCode.internal_error.value)


@cbv.cbv(router)
class FileManifestQuery:
    """List template attributes for files."""

    current_identity: dict = Depends(jwt_required)

    @router.post(
        '/file/manifest/query',
        summary='List template attributes for file',
    )
    async def post(self, request: Request):  # noqa: C901
        api_response = APIResponse()
        data = await request.json()
        if 'geid_list' not in data:
            api_response.set_code(EAPIResponseCode.bad_request)
            api_response.set_result('Missing required field: geid_list')
            return api_response.json_response()

        geid_list = data.get('geid_list')
        results = {}
        try:
            for geid in geid_list:
                entity = await async_get_entity_by_id(geid)
                entity_attributes = entity['extended']['extra'].get('attributes')
                if entity_attributes:
                    if not await has_file_permission(ConfigClass.AUTH_SERVICE, entity, 'view', self.current_identity):
                        api_response.set_code(EAPIResponseCode.forbidden)
                        api_response.set_result('Permission denied')
                        return api_response.json_response()
                    template_id = list(entity['extended']['extra']['attributes'].keys())[0]
                    async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                        url = f'{ConfigClass.METADATA_SERVICE}template/{template_id}/'
                        response = await client.get(url)

                    if response.status_code != 200:
                        api_response.set_code(EAPIResponseCode.not_found)
                        api_response.set_error_msg('Attribute template not found')
                        return api_response.json_response()
                    attributes = []
                    extended_id = entity['extended']['id']
                    template_info = response.json()['result']
                    template_name = template_info['name']
                    for attr, value in entity_attributes[template_id].items():
                        attr_info = next(item for item in template_info['attributes'] if item['name'] == attr)
                        attribute = {
                            'id': extended_id,
                            'name': attr,
                            'manifest_name': template_name,
                            'value': value,
                            'type': attr_info['type'],
                            'optional': attr_info['optional'],
                            'manifest_id': template_id,
                        }
                        attributes.append(attribute)
                    results[geid] = attributes
                else:
                    results[geid] = {}

            api_response.set_code(EAPIResponseCode.success)
            api_response.set_result(results)
            return api_response.json_response()
        except Exception as e:
            logger.error(f'Error when calling metadata service: {e}')
            error_msg = {'result': str(e)}
            return JSONResponse(content=error_msg, status_code=EAPIResponseCode.internal_error.value)


@cbv.cbv(router)
class AttachAttributes:
    """Attach attributes to files or folders (bequeath)"""

    current_identity: dict = Depends(jwt_required)

    @router.post(
        '/file/attributes/attach',
        summary='Attach attributes to files or folders',
    )
    async def post(self, request: Request):  # noqa: C901
        api_response = APIResponse()
        required_fields = ['manifest_id', 'item_ids', 'attributes', 'project_code']
        data = await request.json()
        payload = {'items': []}
        responses = {'result': []}
        for field in required_fields:
            if field not in data:
                api_response.set_code(EAPIResponseCode.bad_request)
                api_response.set_result(f'Missing required field: {field}')
                return api_response.json_response()

        item_ids = data.get('item_ids')
        project_code = data.get('project_code')
        updated_items = []
        try:
            for item_id in item_ids:
                item = await async_get_entity_by_id(item_id)
                if not await has_file_permission(ConfigClass.AUTH_SERVICE, item, 'annotate', self.current_identity):
                    api_response.set_code(EAPIResponseCode.forbidden)
                    api_response.set_result('Permission denied')
                    return api_response.json_response()
                if item['type'] == 'folder':
                    parent_path = item['parent_path']
                    name = item['name']
                    params = {
                        'container_code': project_code,
                        'zone': item['zone'],
                        'recursive': True,
                        'status': ItemStatus.ACTIVE,
                        'type': 'file',
                        'owner': item['owner'],
                        'parent_path': f'{parent_path}/{name}',
                    }
                    async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                        url = f'{ConfigClass.METADATA_SERVICE}items/search/'
                        auth = {'Authorization': request.headers.get('Authorization')}
                        response = await client.get(url, params=params, headers=auth)
                    if response.status_code != 200:
                        api_response.set_code(EAPIResponseCode.internal_error)
                        api_response.set_error_msg('Failed to search for items')
                        return api_response.json_response()
                    else:
                        items_found = response.json()['result']
                        for found in items_found:
                            if data['manifest_id'] in found['extended']['extra']['attributes']:
                                responses['result'].append(
                                    {
                                        'name': found['name'],
                                        'geid': found['id'],
                                        'operation_status': 'TERMINATED',
                                        'error_type': 'attributes_duplicate',
                                    }
                                )
                            else:
                                updated_items.append(found)
                else:
                    updated_items.append(item)
            if updated_items:
                file_ids = []
                for updated in updated_items:
                    update = {
                        'parent': updated['parent'],
                        'parent_path': updated['parent_path'],
                        'tags': updated['extended']['extra']['tags'],
                        'system_tags': updated['extended']['extra']['system_tags'],
                        'type': updated['type'],
                        'attribute_template_id': data['manifest_id'],
                        'attributes': data['attributes'],
                    }
                    payload['items'].append(update)
                    file_ids.append(updated['id'])

                params = {'ids': file_ids}
                async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                    url = f'{ConfigClass.METADATA_SERVICE}items/batch/'
                    response = await client.put(url, params=params, json=payload)

                if response.status_code != 200:
                    logger.error(f'Attaching attributes failed: {response.text}')
                    api_response.set_code(response.status_code)
                    api_response.set_result(response.text)
                    return api_response.json_response()
                for item in response.json()['result']:
                    responses['result'].append(
                        {'name': item['name'], 'geid': item['id'], 'operation_status': 'SUCCEED'}
                    )

            responses['total'] = len(responses['result'])
            api_response.set_result(responses)
            return api_response.json_response()
        except Exception as e:
            logger.error(f'Error when calling metadata service: {e}')
            api_response.set_code(EAPIResponseCode.forbidden)
            api_response.set_result(f'Error when calling metadata service: {e}')
            return api_response.json_response()
