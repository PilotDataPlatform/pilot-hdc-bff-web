# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import re
from typing import Callable
from uuid import uuid4

import pytest
import requests_mock
from async_asgi_testclient import TestClient as TestAsyncClient
from fastapi import APIRouter
from fastapi.testclient import TestClient
from pytest_httpx import HTTPXMock
from testcontainers.redis import RedisContainer

from app.main import create_app
from config import ConfigClass
from config import Settings
from config import get_settings


@pytest.fixture(scope='session')
def test_client(redis):
    ConfigClass.REDIS_URL = redis.url
    app = create_app()
    return TestClient(app)


@pytest.fixture
def test_async_client(redis):
    ConfigClass.REDIS_URL = redis.url
    app = create_app()
    return TestAsyncClient(app)


@pytest.fixture
def requests_mocker():
    kw = {'real_http': True}
    with requests_mock.Mocker(**kw) as m:
        yield m


@pytest.fixture
def jwt_token_admin(mocker, httpx_mock):
    jwt_mock(mocker, httpx_mock, 'admin')


@pytest.fixture
def jwt_token_project_admin(mocker, httpx_mock):
    jwt_mock(mocker, httpx_mock, 'member', 'admin', 'test_project')


@pytest.fixture
def jwt_token_contrib(mocker, httpx_mock):
    jwt_mock(mocker, httpx_mock, 'member', 'contributor', 'test_project')


@pytest.fixture
def jwt_token_collab(mocker, httpx_mock):
    jwt_mock(mocker, httpx_mock, 'member', 'collaborator', 'test_project')


def jwt_mock(mocker, httpx_mock: HTTPXMock, platform_role: str, project_role: str = '', project_code: str = ''):
    if platform_role == 'admin':
        roles = ['platform-admin']
    else:
        roles = [f'{project_code}-{project_role}']
    token = {
        'exp': 1651861167,
        'iat': 1651860867,
        'aud': 'account',
        'sub': 'admin',
        'typ': 'Bearer',
        'acr': '1',
        'realm_access': {'roles': roles},
        'resource_access': {'account': {'roles': []}},
        'email_verified': True,
        'name': 'test test',
        'preferred_username': 'test',
        'given_name': 'test',
        'family_name': 'test',
        'email': 'test@example.com',
        'group': roles,
    }
    mocker.patch('app.auth.get_token', return_value='')
    mocker.patch('jwt.decode', return_value=token)
    mock_data = {
        'result': {
            'id': str(uuid4()),
            'email': 'test@example.com',
            'first_name': 'test@example.com',
            'last_name': 'test@example.com',
            'attributes': {'status': 'active'},
            'role': platform_role,
            'realm_roles': [],
        }
    }
    url = ConfigClass.AUTH_SERVICE + 'admin/user?username=test&exact=true'
    httpx_mock.add_response(method='GET', url=url, json=mock_data)


@pytest.fixture
def has_permission_true(httpx_mock, request):
    url = re.compile('^http://auth/v1/authorize.*$')
    httpx_mock.add_response(method='GET', url=url, json={'result': {'has_permission': True}})


@pytest.fixture
def has_permission_false(httpx_mock):
    url = re.compile('^http://auth/v1/authorize.*$')
    httpx_mock.add_response(method='GET', url=url, json={'result': {'has_permission': False}})


@pytest.fixture
def has_admin_file_permission(httpx_mock):
    url = re.compile(r'^http://auth/v1/authorize\?role=admin&resource=file_any.*$')
    httpx_mock.add_response(method='GET', url=url, json={'result': {'has_permission': True}})
    url = re.compile(r'^http://auth/v1/authorize\?role=admin&resource=file_in_own_namefolder.*$')
    httpx_mock.add_response(method='GET', url=url, json={'result': {'has_permission': True}})


@pytest.fixture
def has_collab_file_permission(httpx_mock):
    url = re.compile(r'^http://auth/v1/authorize\?role=collaborator&resource=file_in_own_namefolder.*$')
    httpx_mock.add_response(method='GET', url=url, json={'result': {'has_permission': True}})
    url = re.compile(r'^http://auth/v1/authorize\?role=collaborator&resource=file_any&zone=core.*$')
    httpx_mock.add_response(method='GET', url=url, json={'result': {'has_permission': True}})
    url = re.compile(r'^http://auth/v1/authorize\?role=collaborator&resource=file_any&zone=greenroom.*$')
    httpx_mock.add_response(method='GET', url=url, json={'result': {'has_permission': False}})


@pytest.fixture
def has_contrib_file_permission(httpx_mock):
    url = re.compile(r'^http://auth/v1/authorize\?role=contributor&resource=file_in_own_namefolder&zone=greenroom.*$')
    httpx_mock.add_response(method='GET', url=url, json={'result': {'has_permission': True}})
    url = re.compile(r'^http://auth/v1/authorize\?role=contributor&resource=file_in_own_namefolder&zone=core.*$')
    httpx_mock.add_response(method='GET', url=url, json={'result': {'has_permission': False}})
    url = re.compile(r'^http://auth/v1/authorize\?role=contributor&resource=file_any.*$')
    httpx_mock.add_response(method='GET', url=url, json={'result': {'has_permission': False}})


@pytest.fixture(scope='session', autouse=True)
def redis():
    with RedisContainer('redis:latest') as redis:
        host = redis.get_container_host_ip()
        port = redis.get_exposed_port(redis.port_to_expose)
        redis.url = f'redis://{host}:{port}'
        yield redis


@pytest.fixture
def find_app_router(test_async_client) -> Callable[[str, str], APIRouter]:
    """Find application router by path and method."""

    def _find_app_router(path: str, method: str) -> APIRouter:
        for route in test_async_client.application.routes:
            if route.path == path and method in route.methods:
                return route

        raise IndexError

    return _find_app_router


@pytest.fixture
def settings() -> Settings:
    settings = get_settings()
    yield settings


pytest_plugins = [
    'tests.fixtures.services.project',
    'tests.fixtures.fake',
]
