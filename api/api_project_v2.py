# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from common import ProjectClient
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi_utils import cbv

from app.auth import jwt_required
from app.logger import logger
from config import ConfigClass
from models.api_response import APIResponse
from services.permissions_service.decorators import PermissionsCheck

router = APIRouter(tags=['Project'])


@cbv.cbv(router)
class RestfulProjectsV2:
    current_identity: dict = Depends(jwt_required)

    @router.post(
        '/projects', summary='Create a project', dependencies=[Depends(PermissionsCheck('project', '*', 'create'))]
    )
    async def post(self, request: Request):
        """This method allow to create a new project in platform.

        Notice that top-level container could only be created by site admin.
        """
        post_data = await request.json()
        _res = APIResponse()
        logger.info(f'Calling API for creating project: {post_data}')

        payload = {
            'name': post_data.get('name'),
            'code': post_data.get('code'),
            'description': post_data.get('description'),
            'is_discoverable': post_data.get('discoverable'),
            'tags': post_data.get('tags'),
        }
        project_client = ProjectClient(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
        project = await project_client.create(**payload)

        if post_data.get('icon'):
            logger.info(f'Uploading icon for project: {post_data["code"]}')
            await project.upload_logo(post_data['icon'])

        return _res.json_response()
