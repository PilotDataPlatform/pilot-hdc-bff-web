# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Annotated

from fastapi import Depends
from fastapi import Request

from app.components.request.http_client import HTTPClient
from config import SettingsDependency


class RequestContext:
    def __init__(self, *, request: Request, client_timeout: int, allowed_headers: set[str] | None = None) -> None:
        self.request = request

        self.allowed_headers = allowed_headers or {
            'forwarded',
            'x-forwarded-for',
            'x-userinfo',
            'authorization',
            'session-id',
        }
        self.headers = {}

        for key, value in self.request.headers.items():
            if key in self.allowed_headers:
                self.headers[key] = value

        self.client = HTTPClient(headers=self.headers, timeout=client_timeout)


def get_request_context(request: Request, settings: SettingsDependency) -> RequestContext:
    return RequestContext(request=request, client_timeout=settings.SERVICE_CLIENT_TIMEOUT)


RequestContextDependency = Annotated[RequestContext, Depends(get_request_context)]
