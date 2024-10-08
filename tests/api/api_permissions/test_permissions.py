# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from uuid import uuid4

from config import ConfigClass

PERMISSIONS_METADATA = {
    'code': 200,
    'error_msg': '',
    'page': 0,
    'total': 12,
    'num_of_pages': 1,
    'result': [
        {
            'id': str(uuid4()),
            'name': 'Fake Permission',
            'category': 'Fake',
            'tooltip': '',
            'resource': 'fake',
            'operation': 'view',
            'zone': 'greenroom',
            'permissions': {
                'collaborator': False,
                'admin': True,
                'contributor': False,
            },
            'project_code': 'test_project',
        },
        {
            'id': str(uuid4()),
            'name': 'Fake Permission 2',
            'category': 'Fake',
            'tooltip': '',
            'resource': 'fake2',
            'operation': 'view',
            'zone': 'core',
            'permissions': {
                'collaborator': True,
                'admin': True,
                'contributor': False,
            },
            'project_code': 'test_project',
        },
    ],
}


class TestPermissions:
    def test_list_permissions_200(self, test_client, httpx_mock, jwt_token_admin, has_permission_true):
        url = ConfigClass.AUTH_SERVICE + 'permissions/metadata?project_code=test_project'
        httpx_mock.add_response(url=url, method='GET', json=PERMISSIONS_METADATA, status_code=200)
        payload = {
            'project_code': 'test_project',
        }
        response = test_client.get('/v1/permissions/metadata', params=payload)
        assert response.status_code == 200

    def test_list_permissions_different_status_code_400(
        self, test_client, httpx_mock, jwt_token_admin, has_permission_true
    ):
        url = ConfigClass.AUTH_SERVICE + 'permissions/metadata?project_code=test_project'
        httpx_mock.add_response(url=url, method='GET', json={}, status_code=400)
        payload = {
            'project_code': 'test_project',
        }
        response = test_client.get('/v1/permissions/metadata', params=payload)
        assert response.status_code == 400

    def test_list_permissions_exception_500(self, test_client, httpx_mock, jwt_token_admin, has_permission_true):
        url = ConfigClass.AUTH_SERVICE + 'permissions/metadata?project_code=test_project'
        httpx_mock.add_response(url=url, method='GET', json=None, status_code=200)
        payload = {
            'project_code': 'test_project',
        }
        response = test_client.get('/v1/permissions/metadata', params=payload)
        assert response.status_code == 500
