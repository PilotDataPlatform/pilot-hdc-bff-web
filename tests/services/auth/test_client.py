# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import re

import httpx
import pytest

from app.components.exceptions import APIException
from config import ConfigClass
from services.auth.client import AuthServiceClient


class TestAuth:
    async def test_get_project_roles_success(self, httpx_mock):
        url = re.compile(r'^' + ConfigClass.AUTH_SERVICE + 'permissions/metadata.*$')
        httpx_mock.add_response(
            url=url,
            method='GET',
            json={
                'result': [
                    {
                        'permissions': {
                            'admin': True,
                            'testuser': False,
                        }
                    }
                ]
            },
            status_code=200,
        )
        auth_client = AuthServiceClient(
            ConfigClass.AUTH_SERVICE.replace('/v1/', ''), ConfigClass.SERVICE_CLIENT_TIMEOUT
        )
        result = await auth_client.get_project_roles('test_project')
        assert result == ['admin', 'testuser']

    async def test_get_project_roles_bad_content_response(self, httpx_mock):
        url = re.compile(r'^' + ConfigClass.AUTH_SERVICE + 'permissions/metadata.*$')
        httpx_mock.add_response(url=url, method='GET', status_code=200)
        with pytest.raises(APIException):
            auth_client = AuthServiceClient(
                ConfigClass.AUTH_SERVICE.replace('/v1/', ''), ConfigClass.SERVICE_CLIENT_TIMEOUT
            )
            await auth_client.get_project_roles('test_project')

    async def test_get_project_roles_bad_empty_list_response(self, httpx_mock):
        url = re.compile(r'^' + ConfigClass.AUTH_SERVICE + 'permissions/metadata.*$')
        httpx_mock.add_response(url=url, method='GET', status_code=200, json={})
        with pytest.raises(APIException):
            auth_client = AuthServiceClient(
                ConfigClass.AUTH_SERVICE.replace('/v1/', ''), ConfigClass.SERVICE_CLIENT_TIMEOUT
            )
            await auth_client.get_project_roles('test_project')

    async def test_get_project_roles_response_500(self, httpx_mock):
        url = re.compile(r'^' + ConfigClass.AUTH_SERVICE + 'permissions/metadata.*$')
        httpx_mock.add_response(url=url, method='GET', status_code=500, json={})
        with pytest.raises(httpx.HTTPStatusError):
            auth_client = AuthServiceClient(
                ConfigClass.AUTH_SERVICE.replace('/v1/', ''), ConfigClass.SERVICE_CLIENT_TIMEOUT
            )
            await auth_client.get_project_roles('test_project')
