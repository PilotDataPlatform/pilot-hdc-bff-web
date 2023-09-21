# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from config import ConfigClass


class TestCopyRequest:
    def test_create_copy_request_200(self, test_client, requests_mocker, jwt_token_project_admin, has_permission_true):
        project_code = 'test_project'
        payload = {}
        headers = {'Authorization': ''}
        url = ConfigClass.APPROVAL_SERVICE + f'request/copy/{project_code}'
        requests_mocker.post(url, json={})
        response = test_client.post(f'/v1/request/copy/{project_code}', json=payload, headers=headers)
        assert response.status_code == 200

    def test_create_copy_request_platform_admin_403(
        self, test_client, requests_mocker, jwt_token_admin, has_permission_true
    ):
        project_code = 'test_project'
        payload = {}
        headers = {'Authorization': ''}
        url = ConfigClass.APPROVAL_SERVICE + f'request/copy/{project_code}'
        requests_mocker.post(url, json={}, status_code=500)
        response = test_client.post(f'/v1/request/copy/{project_code}', json=payload, headers=headers)
        assert response.status_code == 403
