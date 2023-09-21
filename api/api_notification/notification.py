# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Any
from typing import Dict

from fastapi import APIRouter
from fastapi import Depends

from api.api_notification.parameters import NotificationFilterParameters
from app.auth import jwt_required
from app.logger import logger
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode
from services.auth.client import AuthServiceClient
from services.auth.client import get_auth_service_client
from services.notification.client import NotificationServiceClient
from services.notification.client import get_notification_service_client

router = APIRouter(tags=['Notifications'])


@router.get('/user-notifications', summary='List notifications for the current user')
async def get_current_user_notifications(
    filter_parameters: NotificationFilterParameters = Depends(),
    current_identity: Dict[str, Any] = Depends(jwt_required),
    auth_service_client: AuthServiceClient = Depends(get_auth_service_client),
    notification_service_client: NotificationServiceClient = Depends(get_notification_service_client),
):
    """List notifications for the current user."""

    try:
        current_role = current_identity['role']
        current_username = current_identity['username']
        params = await filter_parameters.to_notification_service_params(
            current_username, current_role, auth_service_client
        )
        if filter_parameters.is_type_specified:
            notifications = await notification_service_client.get_all_notifications(params)
        else:
            notifications = await notification_service_client.get_user_notifications(params)
        logger.info('Successfully fetched data from notification service')
        return notification_service_client.replace_zone_labels(notifications)
    except Exception as e:
        logger.error(f'Failed to query data from notification service: {e}')
        response = APIResponse()
        response.set_code(EAPIResponseCode.internal_error)
        response.set_result('Failed to query data from notification service')
        return response.json_response()
