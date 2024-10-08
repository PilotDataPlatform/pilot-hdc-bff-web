# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from uuid import uuid4

from config import ConfigClass


async def test_project_update_uploads_logo_if_it_present_in_the_payload(
    mocker, test_async_client, httpx_mock, jwt_token_admin, has_permission_true
):
    project_id = str(uuid4())
    project_code = 'test_project'
    project = {'id': project_id, 'code': project_code}
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.PROJECT_SERVICE}/v1/projects/{project_id}',
        json=project,
    )
    httpx_mock.add_response(
        method='POST',
        url=f'{ConfigClass.PROJECT_SERVICE}/v1/projects/{project_id}/logo',
        json={},
    )
    httpx_mock.add_response(
        method='PATCH',
        url=f'{ConfigClass.PROJECT_SERVICE}/v1/projects/{project_id}',
        json=project,
    )

    headers = {'Authorization': ''}
    body = {'icon': 'image_data'}
    response = await test_async_client.put(f'/v1/containers/{project_id}', headers=headers, json=body)

    assert response.status_code == 200


async def test_get_user_role_stats_of_project(
    mocker, test_async_client, httpx_mock, jwt_token_contrib, has_permission_true
):
    project_id = str(uuid4())
    project_code = 'test_project'
    project = {'id': project_id, 'code': project_code}
    role_response = {'admin': 1, 'contributor': 5, 'collaborator': 10}
    mocker.patch(
        'services.permissions_service.decorators.get_project_code_from_request',
        return_value={'project_code': project_code},
    )

    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.PROJECT_SERVICE}/v1/projects/{project_id}',
        json=project,
    )

    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.AUTH_SERVICE}admin/roles/users/stats?project_code={project_code}',
        json={'result': role_response},
        status_code=200,
    )

    headers = {'Authorization': ''}
    response = await test_async_client.get(f'/v1/containers/{project_id}/roles/users/stats', headers=headers)
    res = response.json()
    assert response.status_code == 200
    assert res['result'] == role_response
