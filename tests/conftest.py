# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import re
from uuid import uuid4

import jwt
import pytest
import requests_mock
from async_asgi_testclient import TestClient as TestAsyncClient
from fastapi.testclient import TestClient
from pytest_httpx import HTTPXMock
from starlette.config import environ
from testcontainers.redis import RedisContainer

environ['CONFIG_CENTER_ENABLED'] = 'false'
environ['CONFIG_CENTER_BASE_URL'] = ''
environ['SITE_DOMAIN'] = 'http://pilot'
environ['PROJECT_NAME'] = 'Pilot'
environ['CORE_ZONE_LABEL'] = 'Core'
environ['GREENROOM_ZONE_LABEL'] = 'Greenroom'
environ['KONG_PATH'] = '/pilot'
environ['KONG_BASE'] = ''
environ['EMAIL_SUPPORT'] = 'support@example.com'
environ['EMAIL_SUPPORT_REPLY_TO'] = 'no-reply@example.com'
environ['EMAIL_ADMIN'] = 'admin@example.com'
environ['EMAIL_HELPDESK'] = 'helpdesk@example.com'
environ['METADATA_SERVICE'] = 'http://metadata:5060'
environ['DATA_OPS_UTIL'] = 'http://dataops_util'
environ['AUTH_SERVICE'] = 'http://auth'
environ['PROVENANCE_SERVICE'] = 'http://provenance'
environ['NOTIFY_SERVICE'] = 'http://notify'
environ['DATAOPS_SERVICE'] = 'http://dataops'
environ['UPLOAD_SERVICE'] = 'http://upload.greenroom'
environ['DATASET_SERVICE'] = 'http://dataset'
environ['DOWNLOAD_SERVICE_CORE'] = 'http://download.core'
environ['DOWNLOAD_SERVICE_GR'] = 'http://download.greenroom'
environ['APPROVAL_SERVICE'] = 'http://approval'
environ['METADATA_SERVICE'] = 'http://metadata'
environ['PROJECT_SERVICE'] = 'http://project'
environ['SEARCH_SERVICE'] = 'http://search'
environ['WORKSPACE_SERVICE'] = 'http://workspace'
environ['KG_SERVICE'] = 'http://kg'
environ['LDAP_URL'] = ''
environ['LDAP_ADMIN_DN'] = ''
environ['LDAP_ADMIN_SECRET'] = ''
environ['LDAP_OU'] = ''
environ['LDAP_DC1'] = ''
environ['LDAP_DC2'] = ''
environ['LDAP_objectclass'] = ''
environ['LDAP_USER_OBJECTCLASS'] = ''
environ['INVITATION_URL_LOGIN'] = ''
environ['RDS_HOST'] = ''
environ['RDS_PORT'] = ''
environ['RDS_DBNAME'] = ''
environ['RDS_USER'] = ''
environ['RDS_PWD'] = ''
environ['RDS_SCHEMA_DEFAULT'] = ''
environ['MINIO_HOST'] = ''
environ['MINIO_ENDPOINT'] = ''
environ['MINIO_ACCESS_KEY'] = ''
environ['MINIO_SECRET_KEY'] = ''
environ['S3_GATEWAY'] = 'false'
environ['KEYCLOAK_REALM'] = 'test'
environ['RESOURCE_REQUEST_ADMIN'] = 'test'
environ['REDIS_HOST'] = 'redis://redis'
environ['REDIS_PASSWORD'] = 'redis'
environ['REDIS_PORT'] = '6379'
environ['ENABLE_USER_CACHE'] = 'false'
environ['ENABLE_CACHE'] = 'false'
environ['PACT_BROKER_URL'] = ''

# These imports are located here because of ConfigClass, which must first consume the above redefined env vars
from app.main import create_app  # noqa: E402
from config import ConfigClass  # noqa: E402
from config import Settings  # noqa: E402
from config import get_settings  # noqa: E402

REDIS_DOCKER_IMAGE = 'docker-registry.ebrains.eu/hdc-services-external/redis:7.2.5'


@pytest.fixture(scope='session')
def test_client(redis_uri):
    ConfigClass.REDIS_URL = redis_uri
    app = create_app()
    return TestClient(app)


@pytest.fixture
def test_async_client(redis_uri):
    ConfigClass.REDIS_URL = redis_uri
    app = create_app()
    return TestAsyncClient(app)


@pytest.fixture
def requests_mocker():
    kw = {'real_http': True}
    with requests_mock.Mocker(**kw) as m:
        yield m


@pytest.fixture
def jwt_token_admin(mocker, httpx_mock):
    return jwt_mock(mocker, httpx_mock, 'admin')


@pytest.fixture
def jwt_token_project_admin(mocker, httpx_mock):
    return jwt_mock(mocker, httpx_mock, 'member', 'admin', 'test_project')


@pytest.fixture
def jwt_token_contrib(mocker, httpx_mock):
    return jwt_mock(mocker, httpx_mock, 'member', 'contributor', 'test_project')


@pytest.fixture
def jwt_token_collab(mocker, httpx_mock):
    return jwt_mock(mocker, httpx_mock, 'member', 'collaborator', 'test_project')


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
    return jwt.encode(mock_data, key='')


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


@pytest.fixture(scope='session')
def redis_uri():
    with RedisContainer(image=REDIS_DOCKER_IMAGE) as redis:
        host = redis.get_container_host_ip()
        port = redis.get_exposed_port(redis.port_to_expose)
        yield f'redis://{host}:{port}'


@pytest.fixture
def settings() -> Settings:
    settings = get_settings()
    yield settings


@pytest.fixture
def non_mocked_hosts() -> list[str]:
    return ['testserver']


pytest_plugins = [
    'tests.fixtures.services.dataset',
    'tests.fixtures.services.project',
    'tests.fixtures.fake',
]
