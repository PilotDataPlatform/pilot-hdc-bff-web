# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import httpx
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi_utils import cbv

from app.auth import jwt_required
from config import ConfigClass
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode
from services.permissions_service.decorators import PermissionsCheck
from services.permissions_service.utils import get_project_code_from_request

router = APIRouter(tags=['Workbench'])


@cbv.cbv(router)
class WorkbenchRestful:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/{project_id}/workbench',
        summary='List workbench entries',
        dependencies=[Depends(PermissionsCheck('workbench', '*', 'view'))],
    )
    async def get(self, project_id: str):
        api_response = APIResponse()
        payload = {
            'project_id': project_id,
        }
        try:
            async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                url = f'{ConfigClass.PROJECT_SERVICE}/v1/workbenches/'
                response = await client.get(url, params=payload)
                response.raise_for_status()
                workbench_result = response.json()['result']

        except httpx.HTTPStatusError as err:
            api_response.set_error_msg(f'Error retrieving from project service: {err}')
            api_response.set_code(response.status_code)
            return api_response.json_response()

        except httpx.RequestError as err:
            api_response.set_error_msg(f'Error connecting to project serivce: {err}')
            api_response.set_code(response.status_code)
            return api_response.json_response()

        except Exception as e:
            api_response.set_error_msg(f'Error calling project: {e}')
            api_response.set_code(EAPIResponseCode.internal_error)
            return api_response.json_response()

        for resource in workbench_result:
            data = {
                'user_id': resource['deployed_by_user_id'],
            }
            try:
                async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                    url = f'{ConfigClass.AUTH_SERVICE}admin/user'
                    response = await client.get(url, params=data)
                    response.raise_for_status()
                    auth_result = response.json()['result']

            except httpx.HTTPStatusError as err:
                api_response.set_error_msg(f'Error retrieving from auth service: {err}')
                api_response.set_code(response.status_code)
                return api_response.json_response()

            except httpx.RequestError as err:
                api_response.set_error_msg(f'Error connecting to auth serivce: {err}')
                api_response.set_code(response.status_code)
                return api_response.json_response()

            except Exception as e:
                api_response.set_error_msg(f'Error calling project: {e}')
                api_response.set_code(EAPIResponseCode.internal_error)
                return api_response.json_response()

            resource['deploy_by_username'] = auth_result['username']

        data = {i['resource']: i for i in workbench_result}

        api_response.set_result(data)
        api_response.set_code(response.status_code)
        return api_response.json_response()

    @router.post(
        '/{project_id}/workbench',
        summary='create a workbench entry',
        dependencies=[Depends(PermissionsCheck('workbench', '*', 'view'))],
    )
    async def post(self, project_id: str, request: Request):
        api_response = APIResponse()
        data = await request.json()
        payload = {
            'project_id': project_id,
            'resource': data.get('workbench_resource'),
            'deployed_by_user_id': self.current_identity['user_id'],
        }
        try:
            async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                url = f'{ConfigClass.PROJECT_SERVICE}/v1/workbenches/'
                response = await client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()

        except httpx.HTTPStatusError as err:
            api_response.set_error_msg(f'Error posting to project service: {err}')
            api_response.set_code(response.status_code)
            return api_response.json_response()

        except httpx.RequestError as err:
            api_response.set_error_msg(f'Error connecting to project serivce: {err}')
            api_response.set_code(response.status_code)
            return api_response.json_response()

        except Exception as e:
            api_response.set_error_msg(f'Error calling project service: {e}')
            api_response.set_code(EAPIResponseCode.internal_error)
            return api_response.json_response()

        api_response.set_result(result)
        api_response.set_code(response.status_code)

        if data.get('workbench_resource') == 'guacamole':
            project_code = await get_project_code_from_request(request)
            payload = {'container_code': project_code}
            try:
                async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                    url = f'{ConfigClass.WORKSPACE_SERVICE}guacamole/project/users'
                    response = await client.post(url, data=payload)
                    response.raise_for_status()
                    result = response.json()

            except httpx.HTTPStatusError as err:
                error = f'Error creating guacmaole users for {project_code}: {err}'
                api_response.set_error_msg(error)
                api_response.set_code(response.status_code)
                return api_response.json_response()

            except httpx.RequestError as err:
                api_response.set_error_msg(f'Error connecting to workspace serivce: {err}')
                api_response.set_code(response.status_code)
                return api_response.json_response()

            except Exception as e:
                api_response.set_error_msg(f'Error calling workspace service: {e}')
                api_response.set_code(EAPIResponseCode.internal_error)
                return api_response.json_response()

        return api_response.json_response()
