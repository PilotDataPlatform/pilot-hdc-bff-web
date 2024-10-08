# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from uuid import uuid4

from config import ConfigClass

PROJECT_DATA = {
    'code': 'unittestproject',
    'name': 'Unit test project',
    'description': 'test',
    'tags': ['test1', 'test2'],
    'is_discoverable': True,
    'icon': 'fake',
}


async def test_create_project_successful(
    test_async_client, requests_mocker, httpx_mock, jwt_token_admin, has_permission_true
):
    payload = PROJECT_DATA.copy()
    json_response = PROJECT_DATA.copy()
    json_response['id'] = str(uuid4())

    project_id = json_response['id']
    httpx_mock.add_response(
        method='POST', url=ConfigClass.PROJECT_SERVICE + f'/v1/projects/{project_id}/logo', json=payload
    )

    httpx_mock.add_response(method='POST', url=ConfigClass.PROJECT_SERVICE + '/v1/projects/', json=json_response)

    headers = {'Authorization': ''}
    response = await test_async_client.post('/v1/projects', json=payload, headers=headers)
    assert response.status_code == 200


def test_create_project_returns_error(test_client, requests_mocker, httpx_mock, jwt_token_admin, has_permission_true):
    payload = PROJECT_DATA.copy()

    httpx_mock.add_response(
        method='POST', url=ConfigClass.PROJECT_SERVICE + '/v1/projects/', json=payload, status_code=500
    )

    headers = {'Authorization': ''}
    response = test_client.post('/v1/projects', json=payload, headers=headers)
    assert response.status_code == 500
