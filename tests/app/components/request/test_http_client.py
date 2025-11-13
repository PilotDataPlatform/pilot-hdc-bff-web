# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import pytest

from app.components.request.http_client import HTTPClient


class TestHTTPClient:

    @pytest.mark.parametrize('method', ['get', 'post', 'put', 'patch', 'delete'])
    async def test_method_merges_headers_from_constructor_and_arguments(self, method, fake, httpx_mock):
        headers_1 = fake.headers(3)
        headers_2 = fake.headers(3)
        url = fake.url()
        http_client = HTTPClient(headers=headers_1, timeout=5)
        httpx_mock.add_response(method=method, url=url)

        function = getattr(http_client, method)
        await function(url, headers=headers_2)

        requests = httpx_mock.get_requests()
        assert len(requests) == 1
        assert (headers_1 | headers_2).items() <= requests[0].headers.items()
