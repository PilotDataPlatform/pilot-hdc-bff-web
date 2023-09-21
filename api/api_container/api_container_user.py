# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Any
from typing import Dict

from common import ProjectClient
from common.project.project_client import ProjectObject
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_utils import cbv
from httpx import AsyncClient

from app.auth import jwt_required
from app.components.exceptions import APIException
from app.logger import logger
from config import ConfigClass
from models.api_response import EAPIResponseCode
from models.user_type import map_role_to_frontend
from resources.utils import add_user_to_ad_group
from resources.utils import remove_user_from_project_group
from services.notifier_services.email_service import SrvEmail
from services.permissions_service.decorators import PermissionsCheck

router = APIRouter(tags=['Container User Actions'])


@cbv.cbv(router)
class ContainerUser:
    current_identity: dict = Depends(jwt_required)

    @router.post(
        '/containers/{project_id}/users/{username}',
        summary='Add user to project',
        dependencies=[Depends(PermissionsCheck('invitation', '*', 'manage'))],
    )
    async def post(self, username: str, project_id: str, request: Request):
        """This method allow container admin to add single user to a specific container with permission."""
        logger.info(f'Call API for adding user {username} to project {project_id}')

        data = await request.json()
        role = data.get('role', None)
        if role is None:
            logger.error('Error: user\'s role is required.')
            return {'result': "User's role is required."}

        project_client = ProjectClient(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
        project = await project_client.get(id=project_id)

        user = await validate_user(username)
        user_email = user['email']

        if user['role'] != 'admin':
            try:
                add_user_to_ad_group(user_email, project.code, logger)
            except Exception as error:
                message = f'Error adding user to group {project.code}: {error}'
                logger.info(message)
                return JSONResponse(content={'result': message}, status_code=500)

        is_updated, response, code = await keycloak_user_role_update(
            'add',
            user_email,
            f'{project.code}-{role}',
            project.code,
            self.current_identity['username'],
        )
        if not is_updated:
            return JSONResponse(content=response, status_code=code)

        title = f'Project {project.code} Notification: New Invitation'
        template = 'user_actions/invite.html'
        send_email_user(user, project, username, role, title, template, self.current_identity)
        return JSONResponse(content={'result': 'success'}, status_code=200)

    @router.put(
        '/containers/{project_id}/users/{username}',
        summary='Update a users role in project',
        dependencies=[Depends(PermissionsCheck('invitation', '*', 'manage'))],
    )
    async def put(self, username: str, project_id: str, request: Request):
        """This method allow user to update user's permission to a specific dataset."""

        logger.info(f'Call API for changing user {username} role in project {project_id}')

        data = await request.json()
        old_role = data.get('old_role', None)
        new_role = data.get('new_role', None)
        is_valid, res_valid, code = validate_payload(
            old_role=old_role, new_role=new_role, username=username, current_identity=self.current_identity
        )
        if not is_valid:
            return JSONResponse(content=res_valid, status_code=code)

        project_client = ProjectClient(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
        project = await project_client.get(id=project_id)

        user = await validate_user(username)
        user_email = user['email']

        is_updated, response, code = await keycloak_user_role_update(
            'change', user_email, f'{project.code}-{new_role}', project.code, self.current_identity['username']
        )
        if not is_updated:
            return JSONResponse(content=response, status_code=code)

        title = f'Project {project.name} Notification: Role Modified'
        template = 'role/update.html'
        send_email_user(user, project, username, new_role, title, template, self.current_identity)
        return JSONResponse(content={'result': 'success'}, status_code=200)

    @router.delete(
        '/containers/{project_id}/users/{username}',
        summary='Remove user from project',
        dependencies=[Depends(PermissionsCheck('invitation', '*', 'manage'))],
    )
    async def delete(self, username: str, project_id: str):
        """This method allow user to remove user's permission to a specific container."""
        logger.info(f'Call API for removing user {username} from project {project_id}')

        user = await validate_user(username)
        user_email = user['email']

        project_client = ProjectClient(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
        project = await project_client.get(id=project_id)
        async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
            response = await client.get(
                ConfigClass.AUTH_SERVICE + 'admin/users/realm-roles', params={'username': username}
            )
            if response.status_code != 200:
                raise Exception(str(response.__dict__))

        project_role = None
        user_roles = response.json().get('result', [])
        for role in user_roles:
            if role.get('name').startswith(project.code + '-'):
                project_role = role.get('name').replace(project.code + '-', '')

        if not project_role:
            raise Exception('Cannot find user permission in project')

        remove_user_from_project_group(project.code, user_email, logger)
        await keycloak_user_role_delete(
            user_email, f'{project.code}-{project_role}', project.code, self.current_identity['username']
        )
        return {'result': 'success'}


def validate_payload(old_role, new_role, username, current_identity):
    if old_role is None or new_role is None:
        logger.error("User's old and new role is required.")
        return False, {'result': "User's old and new role is required."}, 403
    current_user = current_identity['username']
    if current_user == username:
        logger.error('User cannot change their own role.')
        return False, {'result': 'User cannot change their own role.'}, 403
    return True, {}, 200


async def keycloak_user_role_delete(user_email: str, role: str, project_code: str, operator: str):
    parameters = {
        'email': user_email,
        'project_role': role,
        'project_code': project_code,
        'operator': operator,
    }
    async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
        response = await client.delete(ConfigClass.AUTH_SERVICE + 'user/project-role', params=parameters)
        if response.status_code != 200:
            raise Exception('Error assigning project role' + str(response.__dict__))
    return response


async def keycloak_user_role_update(operation: str, user_email: str, role: str, project_code: str, operator: str):
    payload = {
        'realm': ConfigClass.KEYCLOAK_REALM,
        'email': user_email,
        'project_role': role,
        'project_code': project_code,
        'operator': operator,
    }
    async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
        if operation == 'add':
            payload['invite_event'] = True
            response = await client.post(ConfigClass.AUTH_SERVICE + 'user/project-role', json=payload)
        else:
            response = await client.put(ConfigClass.AUTH_SERVICE + 'user/project-role', json=payload)
        if response.status_code != 200:
            return False, {'result': 'Error assigning project role' + str(response.text)}, response.status_code
    return True, None, 200


def send_email_user(
    user: Dict[str, Any],
    project: ProjectObject,
    username: str,
    role: str,
    title: str,
    template: str,
    current_identity: Dict[str, Any],
) -> None:
    try:
        email = user['email']
        inviter_name = current_identity['username']
        inviter_email = current_identity['email']
        project_role = map_role_to_frontend(role)
        SrvEmail().send(
            title,
            [email],
            msg_type='html',
            template=template,
            template_kwargs={
                'username': username,
                'admin_name': inviter_name,
                'inviter_name': inviter_name,
                'inviter_email': inviter_email,
                'project_name': project.name,
                'project_code': project.code,
                'project_role': project_role,
                'role': project_role,
                'user_email': email,
                'login_url': ConfigClass.INVITATION_URL_LOGIN,
                'register_url': ConfigClass.EMAIL_PROJECT_REGISTER_URL,
                'admin_email': ConfigClass.EMAIL_ADMIN,
                'support_email': ConfigClass.EMAIL_SUPPORT,
                'support_url': ConfigClass.EMAIL_PROJECT_SUPPORT_URL,
            },
        )
    except Exception as e:
        logger.error(f'email service: {e}')


async def validate_user(username: str) -> dict:
    payload = {'username': username}
    async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
        response = await client.get(ConfigClass.AUTH_SERVICE + 'admin/user', params=payload)
        if not response.json()['result']:
            raise APIException(status_code=EAPIResponseCode.not_found.value, error_msg='User not found')
    return response.json()['result']
