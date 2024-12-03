# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import jwt as pyjwt
import requests
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_utils import cbv
from httpx import AsyncClient
from starlette.responses import Response

from app.logger import logger
from config import ConfigClass
from models.models_item import ItemStatus
from resources.utils import add_user_to_ad_group
from services.kg.client import KGRole
from services.kg.client import KGServiceClient
from services.kg.client import get_kg_service_client
from services.project.client import ProjectServiceClient
from services.project.client import get_project_service_client

router = APIRouter(tags=['User Activate'])


@cbv.cbv(router)
class ADUserUpdate:
    project_service_client: ProjectServiceClient = Depends(get_project_service_client)
    kg_service_client: KGServiceClient = Depends(get_kg_service_client)

    @router.put(
        '/users',
        summary='Activate AD user account on platform',
    )
    async def put(self, request: Request):  # noqa: C901
        """This method allow user to activate the AD user account on platform."""
        try:
            token = request.headers.get('Authorization')
            token = token.split()[-1]
            decoded = pyjwt.decode(token, options={'verify_signature': False})
            current_username = decoded['preferred_username']
        except Exception as e:
            return {'result': f'JWT user status error {e}'}, 500

        try:
            post_data = await request.json()
            logger.info(f'Calling API for updating AD user: {post_data}')

            email = post_data.get('email', None)
            username = post_data.get('username', None)
            first_name = post_data.get('first_name', None)
            last_name = post_data.get('last_name', None)

            if current_username != username:
                raise Exception(f'The username is not matched: {current_username}')

            if not username or not first_name or not last_name or not email:
                logger.error('[UserUpdateByEmail] Require field email/username/first_name/last_name.')
                return {'result': 'Required information is not sufficient.'}, 400

            has_invite = True
            email = email.lower()
            filters = {'email': email, 'status': 'sent'}
            async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                response = await client.post(ConfigClass.AUTH_SERVICE + 'invitation-list', json={'filters': filters})
            if not response.json()['result']:
                has_invite = False

            if has_invite:
                logger.info('User has invite.')
                invite_detail = response.json()['result'][0]

                if invite_detail['platform_role'] == 'admin':
                    await self.assign_user_role_ad('platform-admin', email=email)
                    await self.bulk_create_name_folder_admin(username)
                else:
                    if invite_detail['project_code']:
                        await self.add_user_to_project(
                            project_code=invite_detail['project_code'],
                            project_role=invite_detail['project_role'],
                            username=username,
                            email=email,
                        )
                invite_id = invite_detail['id']
                async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                    response = await client.put(
                        ConfigClass.AUTH_SERVICE + f'invitation/{invite_id}', json={'status': 'complete'}
                    )

            response = await self.update_user_status(email)
            return response
        except Exception as error:
            logger.error(f'Error when updating user data : {error}')

            return {'result': {}, 'error_msg': str(error)}

    @router.post(
        '/users/default',
    )
    async def post(self, request: Request):
        try:
            token = request.headers.get('Authorization')
            token = token.split()[-1]
            decoded = pyjwt.decode(token, options={'verify_signature': False})
            current_username = decoded['preferred_username']
        except Exception as e:
            return {'result': f'JWT user status error {e}'}, 500

        try:
            post_data = await request.json()
            logger.info(f'Calling API to add user to starting project: {post_data}')

            email = post_data.get('email', None)
            username = post_data.get('username', None)

            if current_username != username:
                raise Exception(f'The username is not matched: {current_username}')

            await self.add_user_to_project(
                project_code=ConfigClass.STARTING_PROJECT_CODE,
                project_role='collaborator',
                username=username,
                email=email,
            )
            async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                await client.post(
                    ConfigClass.AUTH_SERVICE + 'events',
                    json={
                        'target_user': username,
                        'operator': '',
                        'event_type': 'ADDED_TO_TEST_PROJECT',
                        'detail': {'project_code': ConfigClass.STARTING_PROJECT_CODE},
                    },
                )
            return JSONResponse(
                content={'result': f'Successfully added user {username} to starting project'}, status_code=200
            )
        except Exception as error:
            error_msg = f'Error when adding user to starting project: {error}'
            logger.error(error_msg)

            return JSONResponse(content={'result': error_msg}, status_code=500)

    @router.get(
        '/users/default',
    )
    async def get(self, request: Request, username: str):
        try:
            token = request.headers.get('Authorization')
            token = token.split()[-1]
            decoded = pyjwt.decode(token, options={'verify_signature': False})
            current_username = decoded['preferred_username']
        except Exception as e:
            return {'result': f'JWT user status error {e}'}, 500

        try:
            logger.info('Calling API to check if user is a member of starting project')

            if current_username != username:
                raise Exception(f'The username is not matched: {current_username}')

            query = {
                'username': username,
                'exact': True,
            }
            async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                response = await client.get(ConfigClass.AUTH_SERVICE + 'admin/users/realm-roles', params=query)
                data = response.text
                if ConfigClass.STARTING_PROJECT_CODE in data:
                    return Response(status_code=200)
                else:
                    project = await self.project_service_client.get(code=ConfigClass.STARTING_PROJECT_CODE)
                    content = await project.json()
                    return JSONResponse(content=content, status_code=404)
        except Exception as error:
            error_msg = f'Error when adding user to starting project: {error}'
            logger.error(error_msg)

            return JSONResponse(content={'result': error_msg}, status_code=500)

    async def update_user_status(self, email):
        payload = {
            'operation_type': 'enable',
            'user_email': email,
        }
        async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
            response = await client.put(ConfigClass.AUTH_SERVICE + 'user/account', json=payload)
        logger.info('Update user in auth results: %s', response.json())
        if response.status_code != 200:
            logger.info('Done with updating user node')
            raise (Exception('Internal error when updating user data'))
        return JSONResponse(content=response.json(), status_code=200)

    async def assign_user_role_ad(self, role: str, email: str, project_code: str = ''):
        url = ConfigClass.AUTH_SERVICE + 'user/project-role'
        request_payload = {
            'email': email,
            'realm': ConfigClass.KEYCLOAK_REALM,
            'project_role': role,
            'project_code': project_code,
        }
        async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
            response_assign = await client.post(url, json=request_payload)
        if response_assign.status_code != 200:
            raise Exception(f'[Fatal]Assigned project_role Failed: {email}: {role}: {response_assign.text}')

    async def add_user_to_project(self, project_code: str, project_role: str, email: str, username: str):
        project = await self.project_service_client.get(code=project_code)
        await self.assign_user_role_ad(project.code + '-' + project_role, email=email, project_code=project.code)
        await self.bulk_create_folder(folder_name=username, project_code_list=[project.code])
        add_user_to_ad_group(email, project.code, logger)
        kg_role = KGRole(project_role)
        await self.kg_service_client.add_user_to_space(
            project_id=project.id, username=username, params={'role': kg_role.name}
        )

    async def bulk_create_folder(self, folder_name: str, project_code_list: list):
        try:
            logger.info(
                f'bulk creating namespace folder in greenroom \
                    and core for user : {folder_name} under {project_code_list}'
            )
            zone_list = [ConfigClass.GREENROOM_ZONE_LABEL, ConfigClass.CORE_ZONE_LABEL]

            folders = []
            for zone in zone_list:
                for project_code in project_code_list:
                    folders.append(
                        {
                            'name': folder_name,
                            'zone': 0 if zone.lower() == 'greenroom' else 1,
                            'type': 'name_folder',
                            'status': ItemStatus.ACTIVE,
                            'owner': folder_name,
                            'container_code': project_code,
                            'container_type': 'project',
                            'size': 0,
                            'location_uri': '',
                            'version': '',
                        }
                    )
            payload = {'items': folders, 'skip_duplicates': True}
            response = requests.post(
                ConfigClass.METADATA_SERVICE + 'items/batch/', json=payload, timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT
            )
            async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                response = await client.post(ConfigClass.METADATA_SERVICE + 'items/batch/', json=payload)
            if response.status_code == 200:
                logger.info(
                    f'In namespace: {zone}, folders bulk created successfully for user: {folder_name} \
                        under {project_code_list}'
                )
            else:
                error_msg = f'Error calling metadata service for name folder creation: {response.json()}'
                logger.info(error_msg)
                raise Exception(error_msg)

        except Exception as error:
            logger.error(
                f'Error while trying to create namespace folder for user : {folder_name} under {project_code_list} : \
                        {error}'
            )
            raise error

    async def bulk_create_name_folder_admin(self, username):
        try:
            project_code_list = []
            project_result = await self.project_service_client.search()
            projects = project_result['result']
            for project in projects:
                project_code_list.append(project.code)
            await self.bulk_create_folder(folder_name=username, project_code_list=project_code_list)
            return False
        except Exception as error:
            logger.error(f'Error while querying Container details : {error}')
