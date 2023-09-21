# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import uuid

from config import ConfigClass

LIST_RESULT = {
    'result': [
        {
            'id': str(uuid.uuid4()),
            'invitation_code': str(uuid.uuid4()),
            'email': str('test@test.com'),
            'status': 'sent',
        }
    ]
}


def test_get_invite_register_200(test_client, httpx_mock):
    httpx_mock.add_response(
        method='POST',
        url=ConfigClass.AUTH_SERVICE + 'invitation-list',
        status_code=200,
        json=LIST_RESULT,
    )
    invite_code = LIST_RESULT['result'][0]['invitation_code']
    response = test_client.get(ConfigClass.AUTH_SERVICE + f'register/invitation/{invite_code}')
    assert response.status_code == 200


def test_get_invite_register_404(test_client, httpx_mock):
    httpx_mock.add_response(
        method='POST',
        url=ConfigClass.AUTH_SERVICE + 'invitation-list',
        status_code=200,
        json={'result': []},
    )
    invite_code = LIST_RESULT['result'][0]['invitation_code']
    response = test_client.get(ConfigClass.AUTH_SERVICE + f'register/invitation/{invite_code}')
    assert response.status_code == 404


def test_post_invite_register_200(test_client, httpx_mock, mocker):
    invite_id = LIST_RESULT['result'][0]['id']
    httpx_mock.add_response(
        method='POST',
        url=ConfigClass.AUTH_SERVICE + 'invitation-list',
        status_code=200,
        json=LIST_RESULT,
    )

    httpx_mock.add_response(
        method='POST',
        url=ConfigClass.AUTH_SERVICE + 'admin/users',
        status_code=200,
        json={},
    )

    httpx_mock.add_response(
        method='PUT',
        url=ConfigClass.AUTH_SERVICE + f'invitation/{invite_id}',
        status_code=200,
        json={},
    )

    mocker.patch('services.notifier_services.email_service.SrvEmail.async_send', return_value={})
    invite_code = LIST_RESULT['result'][0]['invitation_code']

    payload = {
        'username': 'test',
        'password': '123',
        'first_name': 'Test',
        'last_name': 'Testing',
    }
    response = test_client.post(ConfigClass.AUTH_SERVICE + f'register/invitation/{invite_code}', json=payload)
    assert response.status_code == 200


def test_post_invite_register_404(test_client, httpx_mock, mocker):
    httpx_mock.add_response(
        method='POST',
        url=ConfigClass.AUTH_SERVICE + 'invitation-list',
        status_code=200,
        json={'result': []},
    )

    mocker.patch('services.notifier_services.email_service.SrvEmail.async_send', return_value={})
    invite_code = LIST_RESULT['result'][0]['invitation_code']

    payload = {
        'username': 'test',
        'password': '123',
        'first_name': 'Test',
        'last_name': 'Testing',
    }
    response = test_client.post(ConfigClass.AUTH_SERVICE + f'register/invitation/{invite_code}', json=payload)
    assert response.status_code == 404


def test_post_invite_register_create_user_error_500(test_client, httpx_mock, mocker):
    httpx_mock.add_response(
        method='POST',
        url=ConfigClass.AUTH_SERVICE + 'invitation-list',
        status_code=200,
        json=LIST_RESULT,
    )

    httpx_mock.add_response(
        method='POST',
        url=ConfigClass.AUTH_SERVICE + 'admin/users',
        status_code=500,
        json={},
    )

    mocker.patch('services.notifier_services.email_service.SrvEmail.async_send', return_value={})
    invite_code = LIST_RESULT['result'][0]['invitation_code']

    payload = {
        'username': 'test',
        'password': '123',
        'first_name': 'Test',
        'last_name': 'Testing',
    }
    response = test_client.post(ConfigClass.AUTH_SERVICE + f'register/invitation/{invite_code}', json=payload)
    assert response.status_code == 500


def test_post_invite_register_email_error_500(test_client, httpx_mock, mocker):
    httpx_mock.add_response(
        method='POST',
        url=ConfigClass.AUTH_SERVICE + 'invitation-list',
        status_code=200,
        json=LIST_RESULT,
    )

    httpx_mock.add_response(
        method='POST',
        url=ConfigClass.AUTH_SERVICE + 'admin/users',
        status_code=200,
        json={},
    )

    mocker.patch('services.notifier_services.email_service.SrvEmail.async_send', return_value={}, side_effect=Exception)
    invite_code = LIST_RESULT['result'][0]['invitation_code']

    payload = {
        'username': 'test',
        'password': '123',
        'first_name': 'Test',
        'last_name': 'Testing',
    }
    response = test_client.post(ConfigClass.AUTH_SERVICE + f'register/invitation/{invite_code}', json=payload)
    assert response.status_code == 500


def test_post_invite_register_invite_update_error_500(test_client, httpx_mock, mocker):
    invite_id = LIST_RESULT['result'][0]['id']
    httpx_mock.add_response(
        method='POST',
        url=ConfigClass.AUTH_SERVICE + 'invitation-list',
        status_code=200,
        json=LIST_RESULT,
    )

    httpx_mock.add_response(
        method='POST',
        url=ConfigClass.AUTH_SERVICE + 'admin/users',
        status_code=200,
        json={},
    )

    httpx_mock.add_response(
        method='PUT',
        url=ConfigClass.AUTH_SERVICE + f'invitation/{invite_id}',
        status_code=500,
        json={},
    )

    mocker.patch('services.notifier_services.email_service.SrvEmail.async_send', return_value={})
    invite_code = LIST_RESULT['result'][0]['invitation_code']

    payload = {
        'username': 'test',
        'password': '123',
        'first_name': 'Test',
        'last_name': 'Testing',
    }
    response = test_client.post(ConfigClass.AUTH_SERVICE + f'register/invitation/{invite_code}', json=payload)
    assert response.status_code == 500
