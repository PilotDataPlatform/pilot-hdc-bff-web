# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import httpx
from pact import EachLike
from pact import Format
from pact import Like

test_user_information_api = 'admin/user'
test_user_api = 'admin/users'
test_realm_roles_api = 'admin/users/realm-roles'
test_query_user_api = 'admin/roles/users'
test_get_user_stats = 'admin/roles/users/stats'


def test_get_user_information_should_return_200(pact_auth_service_init):
    pact = pact_auth_service_init

    query = {'username': 'contracttestaccount'}

    expected = {
        'code': 200,
        'error_msg': '',
        'page': 0,
        'total': Like(1),
        'num_of_pages': Like(1),
        'result': {
            'id': Format().uuid,
            'createdTimestamp': Like(1664396901901),
            'username': 'contracttestaccount',
            'enabled': Like(True),
            'totp': Like(False),
            'emailVerified': Like(False),
            'email': Like('string'),
            'federationLink': Format().uuid,
            'attributes': Like(
                {
                    'LDAP_ENTRY_DN': Like('string'),
                    'last_login': Like('string'),
                    'LDAP_ID': Like('string'),
                    'status': Like('string'),
                    'createTimestamp': Like('string'),
                    'modifyTimestamp': Like('string'),
                }
            ),
            'disableableCredentialTypes': [],
            'requiredActions': [],
            'notBefore': Like(0),
            'access': {
                'manageGroupMembership': Like(True),
                'view': Like(True),
                'mapRoles': Like(True),
                'impersonate': Like(True),
                'manage': Like(True),
            },
            'first_name': Like('name'),
            'last_name': Like('name'),
            'name': Like('name'),
            'role': Like('name'),
        },
    }
    headers = {'Content-Type': 'application/json'}

    pact.given('get user information in auth service').upon_receiving('user information in auth service').with_request(
        method='GET', path='/v1/' + test_user_information_api, query=query, headers=headers
    ).will_respond_with(200, body=expected)
    from config import ConfigClass

    ConfigClass.AUTH_SERVICE = pact.uri + '/v1/'
    with pact:
        res = httpx.get(
            url=ConfigClass.AUTH_SERVICE + test_user_information_api + '?username=contracttestaccount', headers=headers
        )

    assert res.status_code == 200
    pact.verify()


def test_update_user_information_should_return_200(pact_auth_service_init):
    pact = pact_auth_service_init

    payload = {'username': 'contracttestaccount', 'last_login': True}

    expected = {
        'code': 200,
        'error_msg': '',
        'page': 0,
        'total': 1,
        'num_of_pages': 1,
        'result': {'last_login': Like('2023-01-26T18:20:23')},
    }

    headers = {'Content-Type': 'application/json'}

    pact.given('update user information in auth service').upon_receiving(
        'user information in auth service'
    ).with_request(
        method='PUT', path='/v1/' + test_user_information_api, body=payload, headers=headers
    ).will_respond_with(
        200, body=expected
    )
    from config import ConfigClass

    ConfigClass.AUTH_SERVICE = pact.uri + '/v1/'
    with pact:
        res = httpx.put(url=ConfigClass.AUTH_SERVICE + test_user_information_api, json=payload, headers=headers)

    assert res.status_code == 200
    pact.verify()


def test_create_user_should_return_200(pact_auth_service_init):
    pact = pact_auth_service_init

    payload = {
        'username': 'contracttestaccount2',
        'email': 'contract_test+2@email.com',
        'password': 'Contracttestaccount1!',
        'first_name': 'test',
        'last_name': 'account',
        'project_code': '',
        'project_role': '',
    }

    expected = {
        'code': 200,
        'error_msg': '',
        'page': 0,
        'total': 1,
        'num_of_pages': 1,
        'result': {
            'username': 'contracttestaccount2',
            'email': 'contract_test+2@email.com',
            'first_name': 'test',
            'last_name': 'account',
        },
    }

    headers = {'Content-Type': 'application/json'}

    pact.given('create user in FreeIPA in auth service').upon_receiving(
        'user information in auth service'
    ).with_request(method='POST', path='/v1/' + test_user_api, body=payload, headers=headers).will_respond_with(
        200, body=expected
    )
    from config import ConfigClass

    ConfigClass.AUTH_SERVICE = pact.uri + '/v1/'
    with pact:
        res = httpx.post(url=ConfigClass.AUTH_SERVICE + test_user_api, json=payload, headers=headers)

    assert res.status_code == 200
    pact.verify()


def test_get_user_realm_role_should_return_200(pact_auth_service_init):
    pact = pact_auth_service_init

    query = {
        'username': 'contracttestaccount',
    }

    expected = {
        'code': 200,
        'error_msg': '',
        'page': 0,
        'total': 1,
        'num_of_pages': 1,
        'result': EachLike(
            {
                'id': Format().uuid,
                'name': Like('contrattestproject-admin'),
                'composite': Like(False),
                'clientRole': Like(False),
                'containerId': Like('pilot'),
            },
        ),
    }
    headers = {'Content-Type': 'application/json'}

    pact.given('list users realm in auth service').upon_receiving('user information in auth service').with_request(
        method='GET', path='/v1/' + test_realm_roles_api, query=query, headers=headers
    ).will_respond_with(200, body=expected)
    from config import ConfigClass

    ConfigClass.AUTH_SERVICE = pact.uri + '/v1/'
    with pact:
        res = httpx.get(url=ConfigClass.AUTH_SERVICE + test_realm_roles_api, params=query, headers=headers)

    assert res.status_code == 200
    pact.verify()


def test_query_user_by_user_roles_should_return_200(pact_auth_service_init):
    pact = pact_auth_service_init

    payload = {'role_names': ['contrattestproject-admin']}

    expected = {
        'code': 200,
        'error_msg': '',
        'page': 0,
        'total': Like(3),
        'num_of_pages': Like(1),
        'result': EachLike(
            {
                'id': Format().uuid,
                'name': Like('string'),
                'username': Like('string'),
                'first_name': Like('string'),
                'last_name': Like('string'),
                'email': Like('string'),
                'permission': Like('string'),
                'time_created': Like('2022-09-28T16:28:05'),
            }
        ),
    }

    headers = {'Content-Type': 'application/json'}

    pact.given('query user by user role in auth service').upon_receiving(
        'user information in auth service'
    ).with_request(method='POST', path='/v1/' + test_query_user_api, body=payload, headers=headers).will_respond_with(
        200, body=expected
    )
    from config import ConfigClass

    ConfigClass.AUTH_SERVICE = pact.uri + '/v1/'
    with pact:
        res = httpx.post(url=ConfigClass.AUTH_SERVICE + test_query_user_api, json=payload, headers=headers)

    assert res.status_code == 200
    pact.verify()


def test_get_user_stats_in_project_should_return_200(pact_auth_service_init):
    pact = pact_auth_service_init

    query = {
        'project_code': 'contrattestproject',
    }

    expected = {
        'code': 200,
        'error_msg': '',
        'page': 0,
        'total': Like(1),
        'num_of_pages': Like(1),
        'result': {'admin': Like(1), 'contributor': Like(1), 'collaborator': Like(0)},
    }

    headers = {'Content-Type': 'application/json'}

    pact.given('get user statistics in project in auth service').upon_receiving(
        'user information in auth service'
    ).with_request(method='GET', path='/v1/' + test_get_user_stats, query=query, headers=headers).will_respond_with(
        200, body=expected
    )
    from config import ConfigClass

    ConfigClass.AUTH_SERVICE = pact.uri + '/v1/'
    with pact:
        res = httpx.get(url=ConfigClass.AUTH_SERVICE + test_get_user_stats, params=query, headers=headers)

    assert res.status_code == 200
    pact.verify()
