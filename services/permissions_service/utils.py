# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.
from json import JSONDecodeError

from common import ProjectClient
from fastapi import Request

from app.logger import logger
from config import ConfigClass


async def get_project_code_from_request(request: Request):  # noqa: C901
    logger.warning(
        f'Brute force parsing of project from request is deprecated, '
        f'consider refactoring for {request.method} {request.url}'
    )

    if request.method in ['PUT', 'POST', 'PATCH']:
        try:
            data = await request.json()
        except JSONDecodeError:
            data = request.query_params
    elif request.method == 'DELETE':
        data = request.query_params
        if not data:
            try:
                data = await request.json()
            except Exception:
                pass
    else:
        data = request.query_params

    project_client = ProjectClient(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
    if 'project_code' in data:
        return data['project_code']
    if 'container_code' in data:
        return data['container_code']
    if 'project_geid' in data:
        logger.warning(f'Usage of "project_geid" is deprecated, consider removing from {request.method} {request.url}')
        project = await project_client.get(id=data['project_geid'])
        return project.code
    if 'project_id' in data:
        project = await project_client.get(id=data['project_id'])
        return project.code
    kwargs = request.path_params
    if 'project_code' in kwargs:
        return kwargs['project_code']
    if 'project_geid' in kwargs:
        logger.warning(f'Usage of "project_geid" is deprecated, consider removing from {request.method} {request.url}')
        project = await project_client.get(id=kwargs['project_geid'])
        return project.code
    if 'project_id' in kwargs:
        project = await project_client.get(id=kwargs['project_id'])
        return project.code
