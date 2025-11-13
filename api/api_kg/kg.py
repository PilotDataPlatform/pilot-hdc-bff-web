# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Any

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi import Response
from fastapi.responses import JSONResponse
from multidict import MultiDict

from services.kg.client import KGServiceClient
from services.kg.client import get_kg_service_client
from services.permissions_service.decorators import DatasetPermission
from services.permissions_service.decorators import PermissionsCheck

router = APIRouter(tags=['Knowledge Graph'])


@router.get(
    '/kg/spaces',
    summary='List KG spaces',
)
async def list_spaces(
    request: Request, kg_service_client: KGServiceClient = Depends(get_kg_service_client)
) -> JSONResponse:
    """List spaces for user."""
    headers = {'Authorization': request.headers.get('Authorization')}
    response = await kg_service_client.list_available_spaces(params=MultiDict(request.query_params), headers=headers)
    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.post(
    '/kg/spaces',
    summary='Check a list of spaces',
)
async def check_spaces(
    request: Request, body: dict[str, Any], kg_service_client: KGServiceClient = Depends(get_kg_service_client)
) -> JSONResponse:
    """List spaces for user."""

    response = await kg_service_client.check_existing_spaces(json=body, params=MultiDict(request.query_params))
    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.get(
    '/kg/spaces/{space}',
    summary='Get space information',
)
async def get_space(
    request: Request, space: str, kg_service_client: KGServiceClient = Depends(get_kg_service_client)
) -> JSONResponse:
    """Get space information."""

    response = await kg_service_client.get_space_by_id(space=space, params=MultiDict(request.query_params))
    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.post(
    '/kg/spaces/create',
    summary='Create new KG space',
)
async def create_space(
    request: Request, kg_service_client: KGServiceClient = Depends(get_kg_service_client)
) -> Response:
    """Create new KG space with any given name."""
    response = await kg_service_client.create_new_space(params=MultiDict(request.query_params))
    return Response(status_code=response.status_code)


@router.post(
    '/kg/spaces/create/project/{project_code}',
    summary='Create new KG space for project',
    dependencies=[Depends(PermissionsCheck('project', '*', 'view'))],
)
async def create_space_for_project(
    request: Request, project_code: str, kg_service_client: KGServiceClient = Depends(get_kg_service_client)
) -> Response:
    """Create new KG space for project with project code as a name."""
    headers = {'Authorization': request.headers.get('Authorization')}
    response = await kg_service_client.create_new_space_for_project(
        project_code=project_code, params=MultiDict(request.query_params), headers=headers
    )
    return Response(status_code=response.status_code)


@router.post(
    '/kg/spaces/create/dataset/{dataset_code}',
    summary='Create new KG space for dataset',
    dependencies=[Depends(DatasetPermission())],
)
async def create_space_for_dataset(
    request: Request, dataset_code: str, kg_service_client: KGServiceClient = Depends(get_kg_service_client)
) -> Response:
    """Create new KG space for dataset with dataset code as a name."""
    headers = {'Authorization': request.headers.get('Authorization')}
    response = await kg_service_client.create_new_space_for_dataset(
        dataset_code=dataset_code, params=MultiDict(request.query_params), headers=headers
    )
    return Response(status_code=response.status_code)


@router.get(
    '/kg/metadata',
    summary='List metadata',
)
async def list_metadata(
    request: Request, kg_service_client: KGServiceClient = Depends(get_kg_service_client)
) -> JSONResponse:
    """List metadata."""
    headers = {'Authorization': request.headers.get('Authorization')}
    response = await kg_service_client.list_metadata(params=MultiDict(request.query_params), headers=headers)
    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.post(
    '/kg/metadata',
    summary='Check a list of metadata',
)
async def check_metadata(
    request: Request, body: dict[str, Any], kg_service_client: KGServiceClient = Depends(get_kg_service_client)
) -> JSONResponse:
    """Check a list of metadata."""
    response = await kg_service_client.check_existing_metadata(json=body, params=MultiDict(request.query_params))
    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.get(
    '/kg/metadata/{metadata_id}',
    summary='Get metadata information',
)
async def get_metadata(
    request: Request, metadata_id: str, kg_service_client: KGServiceClient = Depends(get_kg_service_client)
) -> JSONResponse:
    """Get metadata information."""

    response = await kg_service_client.get_metadata_by_id(
        metadata_id=metadata_id, params=MultiDict(request.query_params)
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.post(
    '/kg/metadata/upload',
    summary='Upload new metadata to KG',
)
async def upload_metadata(
    request: Request, body: dict[str, Any], kg_service_client: KGServiceClient = Depends(get_kg_service_client)
) -> JSONResponse:
    """Upload new metadata to KG space."""
    headers = {'Authorization': request.headers.get('Authorization')}
    response = await kg_service_client.upload_metadata(
        json=body, params=MultiDict(request.query_params), headers=headers
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.get(
    '/kg/metadata/upload/{kg_instance_id}/{dataset_id}',
    summary='Upload new metadata to dataset from KG',
)
async def upload_metadata_from_kg(
    request: Request,
    kg_instance_id: str,
    dataset_id: str,
    kg_service_client: KGServiceClient = Depends(get_kg_service_client),
) -> JSONResponse:
    headers = {'Authorization': request.headers.get('Authorization')}
    response = await kg_service_client.upload_metadata_from_kg(
        kg_instance_id=kg_instance_id, dataset_id=dataset_id, params=MultiDict(request.query_params), headers=headers
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.get(
    '/kg/metadata/refresh/{metadata_id}',
    summary='Refresh metadata from KG',
)
async def refresh_metadata_from_kg(
    request: Request,
    metadata_id: str,
    kg_service_client: KGServiceClient = Depends(get_kg_service_client),
) -> JSONResponse:
    headers = {'Authorization': request.headers.get('Authorization')}
    response = await kg_service_client.refresh_metadata_from_kg(
        metadata_id=metadata_id, params=MultiDict(request.query_params), headers=headers
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.get(
    '/kg/metadata/refresh/dataset/{dataset_id}',
    summary='Refresh metadata from KG',
)
async def bulk_refresh_metadata_from_kg(
    request: Request,
    dataset_id: str,
    kg_service_client: KGServiceClient = Depends(get_kg_service_client),
) -> JSONResponse:
    headers = {'Authorization': request.headers.get('Authorization')}
    response = await kg_service_client.bulk_refresh_metadata_from_kg(
        dataset_id=dataset_id, params=MultiDict(request.query_params), headers=headers
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.put(
    '/kg/metadata/update/{metadata_id}',
    summary='Update existing metadata on KG',
)
async def update_metadata(
    request: Request,
    metadata_id: str,
    body: dict[str, Any],
    kg_service_client: KGServiceClient = Depends(get_kg_service_client),
) -> JSONResponse:
    """Update existing metadata or upload a new instance to KG."""
    headers = {'Authorization': request.headers.get('Authorization')}
    response = await kg_service_client.update_metadata(
        metadata_id=metadata_id, json=body, params=MultiDict(request.query_params), headers=headers
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.put(
    '/kg/metadata/update/dataset/{dataset_id}',
    summary='Bulk update existing metadata on KG',
)
async def bulk_update_metadata(
    request: Request,
    dataset_id: str,
    kg_service_client: KGServiceClient = Depends(get_kg_service_client),
) -> JSONResponse:
    """Update existing metadata or upload a new instance to KG."""
    headers = {'Authorization': request.headers.get('Authorization')}
    response = await kg_service_client.bulk_update_metadata(
        dataset_id=dataset_id, params=MultiDict(request.query_params), headers=headers
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.delete(
    '/kg/metadata/delete/{metadata_id}',
    summary='Delete existing metadata in KG',
)
async def delete_metadata(
    request: Request,
    metadata_id: str,
    kg_service_client: KGServiceClient = Depends(get_kg_service_client),
) -> Response:
    """Delete existing metadata in KG."""
    headers = {'Authorization': request.headers.get('Authorization')}
    response = await kg_service_client.delete_metadata(
        metadata_id=metadata_id, params=MultiDict(request.query_params), headers=headers
    )
    return Response(status_code=response.status_code)


@router.get(
    '/kg/users/{space}',
    summary='List space users',
)
async def list_users(
    request: Request, space: str, kg_service_client: KGServiceClient = Depends(get_kg_service_client)
) -> JSONResponse:
    """List space's users."""
    headers = {'Authorization': request.headers.get('Authorization')}
    response = await kg_service_client.list_space_users(
        space=space, params=MultiDict(request.query_params), headers=headers
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.post(
    '/kg/users/{project_id}/{username}',
    summary='Add user to all the projects datasets',
    dependencies=[Depends(PermissionsCheck('project', '*', 'view'))],
)
async def add_user(
    request: Request,
    project_id: str,
    username: str,
    kg_service_client: KGServiceClient = Depends(get_kg_service_client),
) -> Response:
    """Add new user to all the projects datasets."""

    response = await kg_service_client.add_user_to_space(
        project_id=project_id, username=username, params=MultiDict(request.query_params)
    )
    return Response(status_code=response.status_code)


@router.delete(
    '/kg/users/{project_id}/{username}',
    summary='Remove user from all the projects datasets',
    dependencies=[Depends(PermissionsCheck('project', '*', 'view'))],
)
async def remove_user(
    request: Request,
    project_id: str,
    username: str,
    kg_service_client: KGServiceClient = Depends(get_kg_service_client),
) -> Response:
    """Remove user from all the projects datasets."""

    response = await kg_service_client.remove_user_from_space(
        project_id=project_id, username=username, params=MultiDict(request.query_params)
    )
    return Response(status_code=response.status_code)


@router.put(
    '/kg/users/{project_id}/{username}',
    summary='Update user role in all the projects datasets',
    dependencies=[Depends(PermissionsCheck('project', '*', 'view'))],
)
async def update_user(
    request: Request,
    project_id: str,
    username: str,
    kg_service_client: KGServiceClient = Depends(get_kg_service_client),
) -> Response:
    """Update user role in all the projects datasets."""

    response = await kg_service_client.update_user_role_for_space(
        project_id=project_id, username=username, params=MultiDict(request.query_params)
    )
    return Response(status_code=response.status_code)
