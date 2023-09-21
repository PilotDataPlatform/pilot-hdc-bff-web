# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from pydantic import BaseModel
from pydantic import validator

from app.components.exceptions import APIException
from models.api_response import EAPIResponseCode


class CreateResourceRequest(BaseModel):
    project_id: str
    request_for: str
    message: str


class UpdateResourceRequest(BaseModel):
    connections: list
    container_code: str

    @validator('connections')
    def validate_connections(cls, v):
        for connection in v:
            if sorted(['name', 'permissions', 'operation']) != sorted(connection.keys()):
                raise APIException(
                    error_msg='name, permissions, operation  required for connection dictionary',
                    status_code=EAPIResponseCode.bad_request.value,
                )
            for permission in connection['permissions']:
                if permission not in ['READ', 'UPDATE', 'DELETE']:
                    raise APIException(error_msg='Invalid permission', status_code=EAPIResponseCode.bad_request.value)
            if connection['operation'] not in ['add', 'remove']:
                raise APIException(error_msg='Invalid operation', status_code=EAPIResponseCode.bad_request.value)
        return v
