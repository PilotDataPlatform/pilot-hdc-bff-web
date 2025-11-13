# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from enum import Enum
from typing import Any

from fastapi import Query
from pydantic import BaseModel

from services.auth.client import AuthServiceClient


class NotificationType(str, Enum):
    """Available notification types."""

    PIPELINE = 'pipeline'
    COPY_REQUEST = 'copy-request'
    ROLE_CHANGE = 'role-change'
    PROJECT = 'project'
    MAINTENANCE = 'maintenance'

    def __str__(self) -> str:
        return self.value


class NotificationFilterParameters(BaseModel):
    """Query parameters for notifications filtering."""

    page: int | None = Query(default=None)
    page_size: int | None = Query(default=None)
    sort_by: str | None = Query(default=None)
    sort_order: str | None = Query(default=None)
    type: NotificationType | None = Query(default=None)

    class Config:
        use_enum_values = True

    @property
    def is_type_specified(self) -> bool:
        return self.type is not None

    async def to_notification_service_params(
        self, current_username: str, current_role: str, auth_service_client: AuthServiceClient
    ) -> dict[str, Any]:
        params = self.dict(exclude_none=True)

        if not self.is_type_specified:
            params['recipient_username'] = current_username
            if current_role != 'admin':
                project_codes = await auth_service_client.get_project_codes_where_user_has_role(current_username)
                params['project_code_any'] = ','.join(project_codes)
        elif self.type == NotificationType.PROJECT:
            if current_role != 'admin':
                project_codes = await auth_service_client.get_project_codes_where_user_has_role(current_username)
                params['project_code_any'] = ','.join(project_codes)
        elif self.type == NotificationType.MAINTENANCE:
            pass
        elif self.type in [NotificationType.PIPELINE, NotificationType.COPY_REQUEST, NotificationType.ROLE_CHANGE]:
            params['recipient_username'] = current_username
        else:
            raise ValueError('unsupported notification type')

        return params
