# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Any
from typing import Dict
from typing import Union
from uuid import UUID

from common.project.project_client import ProjectObject
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi import Response
from starlette.datastructures import MultiDict

from api.api_announcement.dependencies import admin_role_required
from api.api_announcement.dependencies import get_project
from api.api_announcement.schemas import ProjectAnnouncementCreateSchema
from app.auth import jwt_required
from services.notification.client import NotificationServiceClient
from services.notification.client import get_notification_service_client
from services.permissions_service.decorators import PermissionsCheck

router = APIRouter(tags=['Announcements'])


@router.get(
    '/project/{project_code}/announcements/',
    summary='List project announcements',
    dependencies=[Depends(PermissionsCheck('project', '*', 'view'))],
)
async def list_project_announcements(
    request: Request,
    project: ProjectObject = Depends(get_project),
    notification_service_client: NotificationServiceClient = Depends(get_notification_service_client),
) -> Dict[str, Any]:
    """List announcements for project.

    The "project" type notifications are queried using the notification service.
    """

    params = MultiDict(request.query_params)
    response = await notification_service_client.list_project_notifications(project.code, params)
    return response.json()


@router.post(
    '/project/{project_code}/announcements/',
    summary='Create project announcement',
    dependencies=[Depends(PermissionsCheck('announcement', '*', 'create'))],
)
async def create_project_announcement(
    body: ProjectAnnouncementCreateSchema,
    project: ProjectObject = Depends(get_project),
    current_identity: Dict[str, Any] = Depends(jwt_required),
    notification_service_client: NotificationServiceClient = Depends(get_notification_service_client),
) -> Union[Response, Dict[str, Any]]:
    """Create announcement for project.

    The "project" type notification is created using the notification service.
    """

    current_username = current_identity['username']
    response = await notification_service_client.create_project_notification(
        project.code, project.name, current_username, body.message
    )
    try:
        return response.json()
    except ValueError:
        return Response(content=response.content, status_code=response.status_code)


@router.get('/maintenance-announcements/', summary='List maintenance announcements')
async def list_maintenance_announcements(
    request: Request,
    current_identity: Dict[str, Any] = Depends(jwt_required),
    notification_service_client: NotificationServiceClient = Depends(get_notification_service_client),
):
    response = await notification_service_client.list_maintenance_announcements(request.query_params)
    return response.json()


@router.get('/maintenance-announcements/{announcement_id}', summary='Get maintenance announcement')
async def get_maintenance_announcement(
    announcement_id: UUID,
    current_identity: Dict[str, Any] = Depends(jwt_required),
    notification_service_client: NotificationServiceClient = Depends(get_notification_service_client),
):
    announcement = await notification_service_client.get_maintenance_announcement(announcement_id)
    return announcement


@router.post('/maintenance-announcements/', summary='Create maintenance announcement')
async def create_maintenance_announcement(
    request: Request,
    current_identity: Dict[str, Any] = Depends(admin_role_required),
    notification_service_client: NotificationServiceClient = Depends(get_notification_service_client),
):
    json = await request.json()
    announcement = await notification_service_client.create_maintenance_announcement(json)
    return announcement


@router.patch('/maintenance-announcements/{announcement_id}', summary='Update maintenance announcement')
async def update_maintenance_announcement(
    announcement_id: UUID,
    request: Request,
    current_identity: Dict[str, Any] = Depends(admin_role_required),
    notification_service_client: NotificationServiceClient = Depends(get_notification_service_client),
):
    json = await request.json()
    announcement = await notification_service_client.update_maintenance_announcement(announcement_id, json)
    return announcement


@router.delete('/maintenance-announcements/{announcement_id}', summary='Delete maintenance announcement')
async def delete_maintenance_announcement(
    announcement_id: UUID,
    current_identity: Dict[str, Any] = Depends(admin_role_required),
    notification_service_client: NotificationServiceClient = Depends(get_notification_service_client),
):
    response = await notification_service_client.delete_maintenance_announcement(announcement_id)
    try:
        return response.json()
    except ValueError:
        return Response(content=response.content, status_code=response.status_code)


@router.post(
    '/maintenance-announcements/{announcement_id}/unsubscribe', summary='Unsubscribe from maintenance announcement'
)
async def unsubscribe_from_maintenance_announcement(
    announcement_id: UUID,
    current_identity: Dict[str, Any] = Depends(jwt_required),
    notification_service_client: NotificationServiceClient = Depends(get_notification_service_client),
):
    current_username = current_identity['username']
    response = await notification_service_client.unsubscribe_from_maintenance_announcement(
        announcement_id, current_username
    )
    try:
        return response.json()
    except ValueError:
        return Response(content=response.content, status_code=response.status_code)
