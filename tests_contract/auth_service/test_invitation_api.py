# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import httpx
from pact import EachLike
from pact import Format
from pact import Like

test_create_invitation_api = 'invitations'
test_get_user_information_api = 'invitation/check/'
test_list_invitations_api = 'invitation-list'
test_update_invitation_api = 'invitation/'
test_check_allowed_invitations_api = 'invitations/external'


def test_create_user_invitation_should_return_200(pact_auth_service_init):
    pact = pact_auth_service_init

    payload = {
        'email': 'contract_test+1@email.com',
        'platform_role': 'member',
        'relationship': {'project_code': 'contrattestproject', 'project_role': 'admin', 'inviter': 'admin'},
        'invited_by': 'admin',
        'inviter_project_role': 'admin',
    }

    expected = {'code': 200, 'error_msg': '', 'page': 0, 'total': 1, 'num_of_pages': 1, 'result': 'success'}

    headers = {'Content-Type': 'application/json'}

    pact.given('create user invitation in auth service').upon_receiving('user invitation in auth service').with_request(
        method='POST', path='/v1/' + test_create_invitation_api, body=payload, headers=headers
    ).will_respond_with(200, body=expected)
    from config import ConfigClass

    ConfigClass.AUTH_SERVICE = pact.uri + '/v1/'
    with pact:
        res = httpx.post(url=ConfigClass.AUTH_SERVICE + test_create_invitation_api, json=payload, headers=headers)

    assert res.status_code == 200
    pact.verify()


def test_get_user_invitation_should_return_200(pact_auth_service_init):
    pact = pact_auth_service_init
    email = 'contract_test%40email.com'

    query = {'project_code': 'contrattestproject'}

    expected = {
        'code': 200,
        'error_msg': '',
        'page': 0,
        'total': Like(1),
        'num_of_pages': Like(1),
        'result': {
            'name': Like('contracttestaccount'),
            'email': Like('string'),
            'status': Like('active'),
            'role': Like('member'),
            'relationship': Like({}),
        },
    }

    headers = {'Content-Type': 'application/json'}

    pact.given('get user information in auth service').upon_receiving('user invitation in auth service').with_request(
        method='GET', path='/v1/' + test_get_user_information_api + email, query=query, headers=headers
    ).will_respond_with(200, body=expected)
    from config import ConfigClass

    ConfigClass.AUTH_SERVICE = pact.uri + '/v1/'
    with pact:
        res = httpx.get(
            url=ConfigClass.AUTH_SERVICE + test_get_user_information_api + email, params=query, headers=headers
        )

    assert res.status_code == 200
    pact.verify()


def test_list_invitations_should_return_200(pact_auth_service_init):
    pact = pact_auth_service_init

    payload = {'page': 0, 'page_size': 25, 'order_by': 'create_timestamp', 'order_type': 'asc', 'filters': {}}

    expected = {
        'code': 200,
        'error_msg': '',
        'page': 0,
        'total': Like(149),
        'num_of_pages': Like(6),
        'result': EachLike(
            {
                'id': Format().uuid,
                'invitation_code': Like('string'),
                'expiry_timestamp': Like('string'),
                'create_timestamp': Like('string'),
                'invited_by': Like('string'),
                'email': Like('string'),
                'platform_role': Like('string'),
                'project_role': Like('string'),
                'project_code': Like('string'),
                'status': Like('string'),
            }
        ),
    }

    headers = {'Content-Type': 'application/json'}

    pact.given('list user invitations in auth service').upon_receiving('user invitation in auth service').with_request(
        method='POST', path='/v1/' + test_list_invitations_api, body=payload, headers=headers
    ).will_respond_with(200, body=expected)
    from config import ConfigClass

    ConfigClass.AUTH_SERVICE = pact.uri + '/v1/'
    with pact:
        res = httpx.post(url=ConfigClass.AUTH_SERVICE + test_list_invitations_api, json=payload, headers=headers)

    assert res.status_code == 200
    pact.verify()


def test_update_user_invitation_should_return_200(pact_auth_service_init):
    pact = pact_auth_service_init
    invitation_id = '498783f5-4b18-45ba-b9c1-e6a7d578173d'

    payload = {'status': 'complete'}

    expected = {'code': 200, 'error_msg': '', 'page': 0, 'total': 1, 'num_of_pages': 1, 'result': 'success'}

    headers = {'Content-Type': 'application/json'}

    pact.given('update invitation status in auth service').upon_receiving(
        'user invitation in auth service'
    ).with_request(
        method='PUT', path='/v1/' + test_update_invitation_api + invitation_id, body=payload, headers=headers
    ).will_respond_with(
        200, body=expected
    )
    from config import ConfigClass

    ConfigClass.AUTH_SERVICE = pact.uri + '/v1/'
    with pact:
        res = httpx.put(
            url=ConfigClass.AUTH_SERVICE + test_update_invitation_api + invitation_id, json=payload, headers=headers
        )

    assert res.status_code == 200
    pact.verify()


def test_check_invitations_should_return_200(pact_auth_service_init):
    pact = pact_auth_service_init

    expected = {
        'code': 200,
        'error_msg': '',
        'page': 0,
        'total': 1,
        'num_of_pages': 1,
        'result': {'allow_external_registration': Like(True)},
    }

    headers = {'Content-Type': 'application/json'}

    pact.given('check external invitation in auth service').upon_receiving(
        'user invitation in auth service'
    ).with_request(method='GET', path='/v1/' + test_check_allowed_invitations_api, headers=headers).will_respond_with(
        200, body=expected
    )
    from config import ConfigClass

    ConfigClass.AUTH_SERVICE = pact.uri + '/v1/'
    with pact:
        res = httpx.get(url=ConfigClass.AUTH_SERVICE + test_check_allowed_invitations_api, headers=headers)

    assert res.status_code == 200
    pact.verify()
