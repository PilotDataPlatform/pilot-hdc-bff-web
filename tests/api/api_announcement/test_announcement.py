# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import json
import re
from uuid import uuid4

import pytest

from api.api_notification.parameters import NotificationType
from config import ConfigClass


@pytest.mark.asyncio
async def test_list_maintenance_announcements_calls_notification_service(mocker, test_async_client, httpx_mock):
    mocker.patch('app.auth.get_current_identity', return_value={'username': 'admin'})
    expected_result = {'result': [{'id': str(uuid4())}]}
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.NOTIFY_SERVICE}/v2/announcements/',
        json=expected_result,
    )

    response = await test_async_client.get('/v1/maintenance-announcements/')

    assert response.status_code == 200
    assert response.json() == expected_result


@pytest.mark.asyncio
async def test_get_maintenance_announcement_calls_notification_service(mocker, test_async_client, httpx_mock):
    mocker.patch('app.auth.get_current_identity', return_value={'username': 'admin'})
    announcement_id = str(uuid4())
    expected_result = {'id': announcement_id}
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.NOTIFY_SERVICE}/v2/announcements/{announcement_id}',
        json=expected_result,
    )

    response = await test_async_client.get(f'/v1/maintenance-announcements/{announcement_id}')

    assert response.status_code == 200
    assert response.json() == expected_result


@pytest.mark.asyncio
async def test_create_maintenance_announcement_calls_notification_service(mocker, test_async_client, httpx_mock):
    mocker.patch('app.auth.get_current_identity', return_value={'role': 'admin'})
    expected_result = {'message': 'some text'}
    httpx_mock.add_response(
        method='POST',
        url=f'{ConfigClass.NOTIFY_SERVICE}/v2/announcements/',
        json=expected_result,
    )

    response = await test_async_client.post('/v1/maintenance-announcements/', json=expected_result)

    assert response.status_code == 200
    assert response.json() == expected_result


@pytest.mark.asyncio
async def test_update_maintenance_announcement_calls_notification_service(mocker, test_async_client, httpx_mock):
    mocker.patch('app.auth.get_current_identity', return_value={'role': 'admin'})
    announcement_id = str(uuid4())
    expected_result = {'id': announcement_id}
    httpx_mock.add_response(
        method='PATCH',
        url=f'{ConfigClass.NOTIFY_SERVICE}/v2/announcements/{announcement_id}',
        json=expected_result,
    )

    response = await test_async_client.patch(f'/v1/maintenance-announcements/{announcement_id}', json=expected_result)

    assert response.status_code == 200
    assert response.json() == expected_result


@pytest.mark.asyncio
async def test_delete_maintenance_announcement_calls_notification_service(mocker, test_async_client, httpx_mock):
    mocker.patch('app.auth.get_current_identity', return_value={'role': 'admin'})
    announcement_id = str(uuid4())
    httpx_mock.add_response(
        method='DELETE',
        url=f'{ConfigClass.NOTIFY_SERVICE}/v2/announcements/{announcement_id}',
        status_code=204,
    )

    response = await test_async_client.delete(f'/v1/maintenance-announcements/{announcement_id}')

    assert response.status_code == 204
    assert response.content == b''


@pytest.mark.asyncio
async def test_unsubscribe_from_maintenance_announcement_calls_notification_service(
    mocker, test_async_client, httpx_mock
):
    username = 'current-user'
    mocker.patch('app.auth.get_current_identity', return_value={'username': username})
    announcement_id = str(uuid4())
    expected_request = {'username': username}

    httpx_mock.add_response(
        method='POST',
        url=f'{ConfigClass.NOTIFY_SERVICE}/v2/announcements/{announcement_id}/unsubscribe',
        match_content=json.dumps(expected_request).encode(),
        status_code=204,
    )

    response = await test_async_client.post(f'/v1/maintenance-announcements/{announcement_id}/unsubscribe')

    assert response.status_code == 204
    assert response.content == b''


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'method,announcement_id', [('post', ''), ('patch', 'announcement_id'), ('delete', 'announcement_id')]
)
async def test_changing_announcements_is_not_allowed_to_not_admin_role(
    method, announcement_id, mocker, test_async_client
):
    mocker.patch('app.auth.get_current_identity', return_value={'role': 'not_admin'})
    func = getattr(test_async_client, method)
    response = await func(f'/v1/maintenance-announcements/{announcement_id}')

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_project_announcements_calls_notification_service(
    mocker, test_async_client, find_app_router, httpx_mock, jwt_token_admin, has_permission_true
):
    project_code = 'test_project'
    expected_response = {'result': [{'id': str(uuid4())}]}

    httpx_mock.add_response(
        method='GET',
        url=re.compile(
            rf'^{ConfigClass.NOTIFY_SERVICE}/v1/all/notifications/\?type=project&project_code_any={project_code}'
        ),
        json=expected_response,
    )

    response = await test_async_client.get(f'/v1/project/{project_code}/announcements/')

    assert response.status_code == 200
    assert response.json() == expected_response


@pytest.mark.asyncio
async def test_list_project_announcements_does_not_check_project_list_for_admin_role(
    mocker, test_async_client, find_app_router, httpx_mock, jwt_token_admin, has_permission_true
):
    project_code = 'test_project'
    expected_response = {'result': [{'id': str(uuid4())}]}

    httpx_mock.add_response(
        method='GET',
        url=re.compile(
            rf'^{ConfigClass.NOTIFY_SERVICE}/v1/all/notifications/\?type=project&project_code_any={project_code}'
        ),
        json=expected_response,
    )

    response = await test_async_client.get(f'/v1/project/{project_code}/announcements/')

    assert response.status_code == 200
    assert response.json() == expected_response


@pytest.mark.asyncio
async def test_create_project_announcement_calls_notification_service(
    mocker, test_async_client, find_app_router, httpx_mock, jwt_token_admin, has_permission_true
):
    username = 'test'
    project_code = 'test_project'
    project_name = None
    message = f'Announcement for <{project_code}>'
    expected_request = {
        'type': NotificationType.PROJECT.value,
        'project_code': project_code,
        'project_name': project_name,
        'announcer_username': username,
        'message': message,
    }

    httpx_mock.add_response(
        method='POST',
        url=f'{ConfigClass.NOTIFY_SERVICE}/v1/all/notifications/',
        match_content=json.dumps(expected_request).encode(),
        status_code=204,
    )

    response = await test_async_client.post(f'/v1/project/{project_code}/announcements/', json={'message': message})

    assert response.status_code == 204
    assert response.content == b''
