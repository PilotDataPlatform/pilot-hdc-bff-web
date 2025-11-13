# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import re
from urllib.parse import quote

import pytest

from api.api_notification.parameters import NotificationType
from config import ConfigClass


async def test_user_notifications_without_type_calls_notification_service_with_user_notification_route(
    mocker, test_async_client, httpx_mock
):
    username = 'current-user'
    mocker.patch('app.auth.get_current_identity', return_value={'username': username, 'role': 'contributor'})
    expected_response = {'result': []}

    httpx_mock.add_response(
        method='GET',
        url=re.compile(rf'^{ConfigClass.AUTH_SERVICE}admin/users/realm-roles\?username={username}'),
        json={'result': [{'name': 'code1-admin'}, {'name': 'code2-contributor'}]},
    )

    httpx_mock.add_response(
        method='GET',
        url=re.compile(
            rf'^{ConfigClass.NOTIFY_SERVICE}/v1/all/notifications/user\?recipient_username={username}'
            + quote('&project_code_any=code1,code2', safe='=&')
        ),
        json=expected_response,
    )

    headers = {'Authorization': ''}
    response = await test_async_client.get('/v1/user-notifications', headers=headers)

    assert response.status_code == 200

    assert response.json() == expected_response


async def test_user_notifications_with_project_type_calls_notification_service_with_additional_project_code_any_param(
    mocker, test_async_client, httpx_mock
):
    username = 'current-user'
    mocker.patch('app.auth.get_current_identity', return_value={'username': username, 'role': 'contributor'})
    expected_response = {'result': []}

    httpx_mock.add_response(
        method='GET',
        url=re.compile(rf'^{ConfigClass.AUTH_SERVICE}admin/users/realm-roles\?username={username}'),
        json={'result': [{'name': 'code1-admin'}, {'name': 'code2-contributor'}]},
    )

    httpx_mock.add_response(
        method='GET',
        url=re.compile(
            rf'^{ConfigClass.NOTIFY_SERVICE}/v1/all/notifications/\?type=project'
            + quote('&project_code_any=code1,code2', safe='=&')
        ),
        json=expected_response,
    )

    params = {'type': NotificationType.PROJECT}
    headers = {'Authorization': ''}
    response = await test_async_client.get('/v1/user-notifications', params=params, headers=headers)

    assert response.status_code == 200

    assert response.json() == expected_response


async def test_user_notifications_with_maintenance_type_calls_notification_service_with_maintenance_type_param(
    mocker, test_async_client, httpx_mock
):
    username = 'current-user'
    mocker.patch('app.auth.get_current_identity', return_value={'username': username, 'role': 'contributor'})
    expected_response = {'result': []}

    httpx_mock.add_response(
        method='GET',
        url=re.compile(rf'^{ConfigClass.NOTIFY_SERVICE}/v1/all/notifications/\?type=maintenance'),
        json=expected_response,
    )

    params = {'type': NotificationType.MAINTENANCE}
    headers = {'Authorization': ''}
    response = await test_async_client.get('/v1/user-notifications', params=params, headers=headers)

    assert response.status_code == 200

    assert response.json() == expected_response


@pytest.mark.parametrize(
    'notification_type', [NotificationType.PIPELINE, NotificationType.COPY_REQUEST, NotificationType.ROLE_CHANGE]
)
async def test_user_notifications_with_type_calls_notification_service_with_proper_type_and_recipient_username_params(
    notification_type, mocker, test_async_client, httpx_mock
):
    username = 'current-user'
    mocker.patch('app.auth.get_current_identity', return_value={'username': username, 'role': 'contributor'})
    expected_response = {'result': []}

    httpx_mock.add_response(
        method='GET',
        url=re.compile(
            rf'^{ConfigClass.NOTIFY_SERVICE}/v1/all/notifications/\?type={notification_type}'
            + f'&recipient_username={username}'
        ),
        json=expected_response,
    )

    params = {'type': notification_type}
    headers = {'Authorization': ''}
    response = await test_async_client.get('/v1/user-notifications', params=params, headers=headers)

    assert response.status_code == 200

    assert response.json() == expected_response


async def test_user_notifications_replaces_zone_numbers_in_response_with_string_values(
    mocker, test_async_client, httpx_mock
):
    mocker.patch('app.auth.get_current_identity', return_value={'username': 'admin', 'role': 'admin'})
    expected_response = {
        'result': [
            {
                'source': {'zone': ConfigClass.GREENROOM_ZONE_LABEL},
                'destination': {'zone': ConfigClass.CORE_ZONE_LABEL},
            },
            {
                'source': {'zone': ConfigClass.GREENROOM_ZONE_LABEL},
                'destination': None,
            },
        ]
    }

    httpx_mock.add_response(
        method='GET',
        url=re.compile(rf'^{ConfigClass.NOTIFY_SERVICE}/v1/all/notifications.*?'),
        json={
            'result': [
                {
                    'source': {'zone': 0},
                    'destination': {'zone': 1},
                },
                {
                    'source': {'zone': 0},
                    'destination': None,
                },
            ]
        },
    )

    params = {'type': NotificationType.PIPELINE}
    headers = {'Authorization': ''}
    response = await test_async_client.get('/v1/user-notifications', params=params, headers=headers)

    assert response.status_code == 200

    assert response.json() == expected_response
