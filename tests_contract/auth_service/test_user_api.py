# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import httpx
from pact import EachLike
from pact import Format
from pact import Like

test_user_status_api = 'user/account'
test_list_users_api = 'users'
test_user_project_role_api = 'user/project-role'
test_add_user_group_api = 'user/group'


def test_update_user_status_should_return_200(pact_auth_service_init):
    pact = pact_auth_service_init

    payload = {'operation_type': 'enable', 'user_email': 'contract_test@email.com', 'operator': 'admin'}

    expected = {
        'code': 200,
        'error_msg': '',
        'page': 0,
        'total': 1,
        'num_of_pages': 1,
        'result': Like('enable user contract_test@email.com'),
    }

    headers = {'Content-Type': 'application/json'}

    pact.given('update user status in auth service').upon_receiving('user information in auth service').with_request(
        method='PUT', path='/v1/' + test_user_status_api, body=payload, headers=headers
    ).will_respond_with(200, body=expected)
    from config import ConfigClass

    ConfigClass.AUTH_SERVICE = pact.uri + '/v1/'
    with pact:
        res = httpx.put(url=ConfigClass.AUTH_SERVICE + test_user_status_api, json=payload, headers=headers)

    assert res.status_code == 200
    pact.verify()


def test_create_user_project_role_should_return_200(pact_auth_service_init):
    pact = pact_auth_service_init

    payload = {
        'email': 'contract_test@email.com',
        'project_role': 'contrattestproject-admin',
        'operator': 'admin',
        'project_code': 'contrattestproject',
        'invite_event': False,
    }

    expected = {'code': 200, 'error_msg': '', 'page': 0, 'total': 1, 'num_of_pages': 1, 'result': 'success'}

    headers = {'Content-Type': 'application/json'}

    pact.given('create user project role in auth service').upon_receiving(
        'user information in auth service'
    ).with_request(
        method='POST', path='/v1/' + test_user_project_role_api, body=payload, headers=headers
    ).will_respond_with(
        200, body=expected
    )
    from config import ConfigClass

    ConfigClass.AUTH_SERVICE = pact.uri + '/v1/'
    with pact:
        res = httpx.post(url=ConfigClass.AUTH_SERVICE + test_user_project_role_api, json=payload, headers=headers)

    assert res.status_code == 200
    pact.verify()


def test_list_user_should_return_200(pact_auth_service_init):
    pact = pact_auth_service_init

    query = {'username': 'contracttestaccount', 'page': '0', 'page_size': '10', 'order_type': 'asc'}

    expected = {
        'code': 200,
        'error_msg': '',
        'page': 0,
        'total': 1,
        'num_of_pages': 1,
        'result': EachLike(
            {
                'id': Format().uuid,
                'name': Like('string'),
                'username': Like('string'),
                'first_name': Like('string'),
                'last_name': Like('string'),
                'email': Like('string'),
                'time_created': Like('2022-09-28T16:28:05'),
                'last_login': Like('2023-01-20T20:59:44'),
                'status': Like('A string'),
                'role': Like('A string'),
            }
        ),
    }
    headers = {'Content-Type': 'application/json'}

    pact.given('list users in auth service').upon_receiving('user information in auth service').with_request(
        method='GET', path='/v1/' + test_list_users_api, query=query, headers=headers
    ).will_respond_with(200, body=expected)
    from config import ConfigClass

    ConfigClass.AUTH_SERVICE = pact.uri + '/v1/'
    with pact:
        res = httpx.get(url=ConfigClass.AUTH_SERVICE + test_list_users_api, params=query, headers=headers)

    assert res.status_code == 200
    pact.verify()


def test_update_user_project_role_should_return_200(pact_auth_service_init):
    pact = pact_auth_service_init

    payload = {
        'email': 'contract_test@email.com',
        'project_role': 'contrattestproject-contributor',
        'operator': 'admin',
        'project_code': 'contrattestproject',
    }

    expected = {'code': 200, 'error_msg': '', 'page': 0, 'total': 1, 'num_of_pages': 1, 'result': 'success'}

    headers = {'Content-Type': 'application/json'}

    pact.given('update user project role in auth service').upon_receiving(
        'user information in auth service'
    ).with_request(
        method='PUT', path='/v1/' + test_user_project_role_api, body=payload, headers=headers
    ).will_respond_with(
        200, body=expected
    )
    from config import ConfigClass

    ConfigClass.AUTH_SERVICE = pact.uri + '/v1/'
    with pact:
        res = httpx.put(url=ConfigClass.AUTH_SERVICE + test_user_project_role_api, json=payload, headers=headers)

    assert res.status_code == 200
    pact.verify()


def test_delete_user_project_role_should_return_200(pact_auth_service_init):
    pact = pact_auth_service_init

    parameters = {
        'email': 'contract_test@email.com',
        'project_role': 'contrattestproject-contributor',
        'operator': 'admin',
        'project_code': 'contrattestproject',
    }

    expected = {'code': 200, 'error_msg': '', 'page': 0, 'total': 1, 'num_of_pages': 1, 'result': 'success'}

    headers = {'Content-Type': 'application/json'}

    pact.given('delete user project role in auth service').upon_receiving(
        'user information in auth service'
    ).with_request(
        method='DELETE', path='/v1/' + test_user_project_role_api, query=parameters, headers=headers
    ).will_respond_with(
        200, body=expected
    )
    from config import ConfigClass

    ConfigClass.AUTH_SERVICE = pact.uri + '/v1/'
    with pact:
        res = httpx.delete(
            url=ConfigClass.AUTH_SERVICE + test_user_project_role_api, params=parameters, headers=headers
        )

    assert res.status_code == 200
    pact.verify()


def test_add_user_to_ldap_group_should_return_200(pact_auth_service_init):
    pact = pact_auth_service_init

    payload = {'operation_type': 'add', 'group_code': 'contrattestproject', 'user_email': 'contract_test@email.com'}

    expected = {
        'code': 200,
        'error_msg': '',
        'page': 0,
        'total': 1,
        'num_of_pages': 1,
        'result': Like('add user contract_test@email.com from ad group'),
    }

    headers = {'Content-Type': 'application/json'}

    pact.given('add user to ldap group in auth service').upon_receiving(
        'user information in auth service'
    ).with_request(
        method='PUT', path='/v1/' + test_add_user_group_api, body=payload, headers=headers
    ).will_respond_with(
        200, body=expected
    )
    from config import ConfigClass

    ConfigClass.AUTH_SERVICE = pact.uri + '/v1/'
    with pact:
        res = httpx.put(url=ConfigClass.AUTH_SERVICE + test_add_user_group_api, json=payload, headers=headers)

    assert res.status_code == 200
    pact.verify()
