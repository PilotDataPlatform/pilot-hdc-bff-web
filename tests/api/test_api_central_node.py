# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from app.components.user.models import CurrentUser
from models.user_type import EUserRole


class TestCopyToCentralNode:

    async def test_init_makes_upload_request_to_dataops_service(
        self, mocker, settings, test_async_client, httpx_mock, fake, has_permission_true
    ):
        username = fake.user_name()
        project_code = fake.project_code()
        realm_roles = [f'{project_code}-{EUserRole.admin.name}']
        session_id = fake.uuid4()
        file_id = fake.uuid4()
        file_node = {
            'id': file_id,
            'container_type': 'project',
            'container_code': project_code,
            'zone': 0,
            'parent_path': 'test',
        }

        mocker.patch(
            'app.auth.get_current_identity',
            return_value=CurrentUser({'role': 'member', 'username': username, 'realm_roles': realm_roles}),
        )
        httpx_mock.add_response(url=f'{settings.METADATA_SERVICE}item/{file_id}/', json={'result': file_node})

        httpx_mock.add_response(method='POST', url=f'{settings.DATAOPS_SERVICE}central-node/upload', json={})

        headers = {'Authorization': ''}
        response = await test_async_client.post(
            '/v1/central-node/upload',
            json={'file_id': file_id, 'session_id': session_id},
            headers=headers,
        )

        assert response.status_code == 200

    async def test_init_returns_forbidden_when_permission_denied(
        self, mocker, settings, test_async_client, httpx_mock, fake, has_permission_false
    ):
        username = fake.user_name()
        project_code = fake.project_code()
        realm_roles = [f'{project_code}-{EUserRole.admin.name}']
        file_id = fake.uuid4()
        file_node = {
            'id': file_id,
            'container_type': 'project',
            'container_code': project_code,
            'zone': 0,
            'parent_path': 'test',
        }

        mocker.patch(
            'app.auth.get_current_identity',
            return_value=CurrentUser({'role': 'member', 'username': username, 'realm_roles': realm_roles}),
        )
        httpx_mock.add_response(url=f'{settings.METADATA_SERVICE}item/{file_id}/', json={'result': file_node})

        headers = {'Authorization': ''}
        response = await test_async_client.post(
            '/v1/central-node/upload',
            json={'file_id': file_id, 'session_id': fake.uuid4()},
            headers=headers,
        )

        assert response.status_code == 403
        assert response.json()['error_msg'] == 'Permission denied'

    async def test_wait_makes_upload_request_to_dataops_service(
        self, mocker, settings, test_async_client, httpx_mock, fake
    ):
        username = fake.user_name()
        project_code = fake.project_code()
        realm_roles = [f'{project_code}-{EUserRole.admin.name}']
        upload_key = fake.sha256()

        mocker.patch(
            'app.auth.get_current_identity',
            return_value=CurrentUser({'role': 'member', 'username': username, 'realm_roles': realm_roles}),
        )
        httpx_mock.add_response(url=f'{settings.DATAOPS_SERVICE}central-node/upload/{upload_key}', json={})

        response = await test_async_client.get(
            f'/v1/central-node/upload/{upload_key}',
            headers={'Authorization': f'Bearer {fake.sha256()}'},
        )

        assert response.status_code == 200
