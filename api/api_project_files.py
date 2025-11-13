# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from collections.abc import Mapping
from typing import Any

from common import has_permission
from common.project.project_client import ProjectObject
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from starlette.datastructures import MultiDict

from app.auth import jwt_required
from app.components.user.models import CurrentUser
from app.logger import logger
from config import ConfigClass
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode
from services.permissions_service.decorators import PermissionsCheck
from services.project.client import ProjectServiceClient
from services.project.client import get_project_service_client
from services.search.client import SearchServiceClient
from services.search.client import get_search_service_client

router = APIRouter(prefix='/project-files', tags=['Project Files'], dependencies=[Depends(jwt_required)])


def get_zone_label(zone: int) -> str:
    """Get zone label for zone number."""

    try:
        return ConfigClass.ZONE_LABEL_MAPPING[zone]
    except KeyError:
        return str(zone)


def get_zone_int(zone: str) -> int:
    """Get zone number for zone label."""

    return ConfigClass.LABEL_ZONE_MAPPING[zone.lower()]


def _replace_zone_labels_in_search_response(response: dict[str, Any]) -> dict[str, Any]:
    """Replace zone numbers with string values."""

    result = response['result']
    for item in result:
        item['zone'] = get_zone_label(item['zone'])

    return response


def _replace_zone_labels_in_size_response(response: dict[str, Any]) -> dict[str, Any]:
    """Replace zone numbers with string values."""
    for dataset in response['data']['datasets']:
        dataset['label'] = get_zone_label(dataset['label'])

    return response


def _add_file_stats_per_zone(zones: dict[str, Any] | None) -> dict[str, Any]:
    stats = {
        'files': {'total_count': 0, 'total_size': 0, 'total_per_zone': {}},
        'activity': {'today_uploaded': 0, 'today_downloaded': 0},
    }

    for zone in zones.keys():
        zone_stats = zones[zone]
        stats['files']['total_count'] += zone_stats['files']['total_count']
        stats['files']['total_size'] += zone_stats['files']['total_size']
        stats['files']['total_per_zone'][zone.lower()] = zone_stats['files']['total_count']
        stats['activity']['today_uploaded'] += zone_stats['activity']['today_uploaded']
        stats['activity']['today_downloaded'] += zone_stats['activity']['today_downloaded']

    return stats


def _compile_file_size_per_zone(zones: dict[str, Any]) -> dict[str, Any]:
    compiled = {'data': {'labels': [], 'datasets': []}}
    for zone in zones:
        zone_data = zones[zone]
        compiled['data']['labels'] = zone_data['data']['labels']
        for i in zone_data['data']['datasets']:
            if zone == ConfigClass.GREENROOM_ZONE_LABEL:
                if i['label'] == 0:
                    compiled['data']['datasets'].append(i)
            else:
                if i['label'] == 1:
                    compiled['data']['datasets'].append(i)

    return compiled


async def compile_file_statistics_for_zone_and_role(
    request, search_service_client, current_identity, project_code
) -> dict[str, Any]:
    username = current_identity['username']

    params = MultiDict(request.query_params)
    result_greenroom = {}
    result_core = {}
    stats_result = {}

    if await has_permission(ConfigClass.AUTH_SERVICE, project_code, 'file_any', 'greenroom', 'view', current_identity):
        result_greenroom = await search_service_client.get_project_statistics(
            project_code, {**params, **{'zone': get_zone_int(ConfigClass.GREENROOM_ZONE_LABEL)}}
        )
    elif await has_permission(
        ConfigClass.AUTH_SERVICE, project_code, 'file_in_own_namefolder', 'greenroom', 'view', current_identity
    ):
        result_greenroom = await search_service_client.get_project_statistics(
            project_code,
            {**params, **{'zone': get_zone_int(ConfigClass.GREENROOM_ZONE_LABEL), 'parent_path': f'{username}%'}},
        )

    if await has_permission(ConfigClass.AUTH_SERVICE, project_code, 'file_any', 'core', 'view', current_identity):
        result_core = await search_service_client.get_project_statistics(
            project_code, {**params, **{'zone': get_zone_int(ConfigClass.CORE_ZONE_LABEL)}}
        )
    elif await has_permission(
        ConfigClass.AUTH_SERVICE, project_code, 'file_in_own_namefolder', 'core', 'view', current_identity
    ):
        result_core = await search_service_client.get_project_statistics(
            project_code,
            {**params, **{'zone': get_zone_int(ConfigClass.CORE_ZONE_LABEL), 'parent_path': f'{username}%'}},
        )

    results = {}
    if result_greenroom:
        results[ConfigClass.GREENROOM_ZONE_LABEL] = result_greenroom
    if result_core:
        results[ConfigClass.CORE_ZONE_LABEL] = result_core
    stats_result = _add_file_stats_per_zone(results)
    return stats_result


async def _ensure_datasets_in_size_response(
    response: dict[str, Any], project_code: str, current_identity
) -> dict[str, Any]:
    """Replace empty datasets with zero values per zone when no entries are available."""

    if response['data']['datasets']:
        return response

    available_zones = set()
    if await has_permission(
        ConfigClass.AUTH_SERVICE, project_code, 'file_in_own_namefolder', 'greenroom', 'view', current_identity
    ):
        available_zones.add(get_zone_int(ConfigClass.GREENROOM_ZONE_LABEL))
    if await has_permission(
        ConfigClass.AUTH_SERVICE, project_code, 'file_in_own_namefolder', 'core', 'view', current_identity
    ):
        available_zones.add(get_zone_int(ConfigClass.CORE_ZONE_LABEL))

    empty_values = [0] * len(response['data']['labels'])
    response['data']['datasets'] = [{'label': zone, 'values': empty_values} for zone in available_zones]

    return response


async def compile_file_size_for_zone_and_role(
    request, search_service_client, current_identity, project_code
) -> dict[str, Any]:
    params = MultiDict(request.query_params)
    size_result = {}
    username = current_identity['username']
    result_greenroom = {}
    result_core = {}

    if await has_permission(ConfigClass.AUTH_SERVICE, project_code, 'file_any', 'greenroom', 'view', current_identity):
        result_greenroom = await search_service_client.get_project_size(project_code, params)
    elif await has_permission(
        ConfigClass.AUTH_SERVICE, project_code, 'file_in_own_namefolder', 'greenroom', 'view', current_identity
    ):
        result_greenroom = await search_service_client.get_project_size(
            project_code, {**params, **{'parent_path': f'{username}%'}}
        )

    if await has_permission(ConfigClass.AUTH_SERVICE, project_code, 'file_any', 'core', 'view', current_identity):
        result_core = await search_service_client.get_project_size(project_code, params)
    elif await has_permission(
        ConfigClass.AUTH_SERVICE, project_code, 'file_in_own_namefolder', 'core', 'view', current_identity
    ):
        result_core = await search_service_client.get_project_size(
            project_code, {**params, **{'parent_path': f'{username}%'}}
        )

    results = {}
    if result_greenroom:
        results[ConfigClass.GREENROOM_ZONE_LABEL] = result_greenroom
    if result_core:
        results[ConfigClass.CORE_ZONE_LABEL] = result_core
    size_result = _compile_file_size_per_zone(results)

    return await _ensure_datasets_in_size_response(size_result, project_code, current_identity)


async def get_project(
    project_code: str, project_service_client: ProjectServiceClient = Depends(get_project_service_client)
) -> ProjectObject:
    """Get project by code as a dependency."""

    return await project_service_client.get(code=project_code)


async def get_params_for_current_identity(
    request: Request, current_identity: dict[str, Any], project_code: str
) -> Mapping[str, Any]:
    """Override search service query params depending on current user role."""

    username = current_identity['username']

    params = MultiDict(request.query_params)

    if 'zone' not in params:
        params['zone'] = ConfigClass.GREENROOM_ZONE_LABEL

    params['zone'] = get_zone_int(params['zone'])

    if await has_permission(
        ConfigClass.AUTH_SERVICE,
        project_code,
        'file_any',
        get_zone_label(params['zone']).lower(),
        'view',
        current_identity,
    ):
        return params
    elif await has_permission(
        ConfigClass.AUTH_SERVICE,
        project_code,
        'file_in_own_namefolder',
        get_zone_label(params['zone']).lower(),
        'view',
        current_identity,
    ):
        params['parent_path'] = f'{username}%'
        return params
    else:
        raise NotImplementedError('Unknown project role')


@router.get('/{project_code}/search', summary='Search through project files.')
async def search(
    request: Request,
    current_identity: CurrentUser = Depends(jwt_required),
    project: ProjectObject = Depends(get_project),
    search_service_client: SearchServiceClient = Depends(get_search_service_client),
):
    """Search through project files."""

    response = APIResponse()

    try:
        params = await get_params_for_current_identity(request, current_identity, project.code)
        params['container_type'] = 'project'
        params['container_code'] = project.code

        result = await search_service_client.get_metadata_items(params)
        logger.info('Successfully fetched data from search service')
        return _replace_zone_labels_in_search_response(result)
    except Exception as e:
        logger.error(f'Failed to query data from search service: {e}')
        response.set_code(EAPIResponseCode.internal_error)
        response.set_result('Failed to query data from search service')
        return response.json_response()


@router.get(
    '/{project_code}/size',
    summary='Get project storage usage.',
    dependencies=[Depends(PermissionsCheck('project', '*', 'view'))],
)
async def size(
    request: Request,
    current_identity: CurrentUser = Depends(jwt_required),
    project: ProjectObject = Depends(get_project),
    search_service_client: SearchServiceClient = Depends(get_search_service_client),
):
    """Get project storage usage."""
    response = APIResponse()
    try:
        project_size = await compile_file_size_for_zone_and_role(
            request, search_service_client, current_identity, project.code
        )
        logger.info('Successfully fetched data from search service')
        return _replace_zone_labels_in_size_response(project_size)
    except Exception as e:
        logger.error(f'Failed to query data from search service: {e}')
        response.set_code(EAPIResponseCode.internal_error)
        response.set_result('Failed to query data from search service')
        return response.json_response()


@router.get(
    '/{project_code}/statistics', summary='Get project statistics on files and transfer activity limited to user.'
)
async def statistics(
    request: Request,
    current_identity: CurrentUser = Depends(jwt_required),
    project: ProjectObject = Depends(get_project),
    search_service_client: SearchServiceClient = Depends(get_search_service_client),
):
    """Get project statistics on files and transfer activity limited to user."""

    try:
        project_statistics = await compile_file_statistics_for_zone_and_role(
            request, search_service_client, current_identity, project.code
        )
        logger.info('Successfully fetched data from search service')
        return project_statistics
    except Exception as e:
        logger.error(f'Failed to query data from search service: {e}')
        response = APIResponse()
        response.set_code(EAPIResponseCode.internal_error)
        response.set_result('Failed to query data from search service')
        return response.json_response()


@router.get(
    '/{project_code}/activity',
    summary='Get project file activity statistic limited to role.',
    dependencies=[Depends(PermissionsCheck('project', '*', 'view'))],
)
async def activity(
    request: Request,
    current_identity: CurrentUser = Depends(jwt_required),
    project: ProjectObject = Depends(get_project),
    search_service_client: SearchServiceClient = Depends(get_search_service_client),
):
    """Get project file activity statistic limited to role."""

    response = APIResponse()
    try:
        params = MultiDict(request.query_params)

        if not await has_permission(
            ConfigClass.AUTH_SERVICE, project.code, 'file_any', 'greenroom', 'view', current_identity
        ):
            params['user'] = current_identity['username']
        if not await has_permission(
            ConfigClass.AUTH_SERVICE, project.code, 'file_any', 'core', 'view', current_identity
        ):
            params['user'] = current_identity['username']

        result = await search_service_client.get_project_activity(project.code, params)
        logger.info('Successfully fetched data from search service')
        return result
    except Exception as e:
        logger.error(f'Failed to query data from search service: {e}')
        response.set_code(EAPIResponseCode.internal_error)
        response.set_result('Failed to query data from search service')
        return response.json_response()
