# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Any

from httpx import URL
from httpx import AsyncClient
from httpx import Response
from httpx._types import HeaderTypes
from httpx._types import QueryParamTypes
from httpx._types import RequestContent
from httpx._types import RequestData
from httpx._types import TimeoutTypes


class HTTPClient:

    def __init__(self, *, headers: HeaderTypes, timeout: TimeoutTypes) -> None:
        self.headers = headers
        self.timeout = timeout

    @property
    def client(self) -> AsyncClient:
        return AsyncClient(headers=self.headers, timeout=self.timeout)

    async def get(
        self,
        url: URL | str,
        *,
        params: QueryParamTypes | None = None,
        headers: HeaderTypes | None = None,
    ) -> Response:
        async with self.client as client:
            return await client.request('GET', url, params=params, headers=headers)

    async def post(
        self,
        url: URL | str,
        *,
        content: RequestContent | None = None,
        data: RequestData | None = None,
        json: Any | None = None,
        params: QueryParamTypes | None = None,
        headers: HeaderTypes | None = None,
    ) -> Response:
        async with self.client as client:
            return await client.request(
                'POST', url, content=content, data=data, json=json, params=params, headers=headers
            )

    async def put(
        self,
        url: URL | str,
        *,
        content: RequestContent | None = None,
        data: RequestData | None = None,
        json: Any | None = None,
        params: QueryParamTypes | None = None,
        headers: HeaderTypes | None = None,
    ) -> Response:
        async with self.client as client:
            return await client.request(
                'PUT', url, content=content, data=data, json=json, params=params, headers=headers
            )

    async def patch(
        self,
        url: URL | str,
        *,
        content: RequestContent | None = None,
        data: RequestData | None = None,
        json: Any | None = None,
        params: QueryParamTypes | None = None,
        headers: HeaderTypes | None = None,
    ) -> Response:
        async with self.client as client:
            return await client.request(
                'PATCH', url, content=content, data=data, json=json, params=params, headers=headers
            )

    async def delete(
        self,
        url: URL | str,
        *,
        json: Any | None = None,
        params: QueryParamTypes | None = None,
        headers: HeaderTypes | None = None,
    ) -> Response:
        async with self.client as client:
            return await client.request('DELETE', url, json=json, params=params, headers=headers)
