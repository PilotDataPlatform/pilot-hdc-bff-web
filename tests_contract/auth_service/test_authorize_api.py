# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import httpx
from pact import Like

test_has_permission_api = 'authorize'


def test_has_permission_should_return_200(pact_auth_service_init):
    pact = pact_auth_service_init

    query = {'role': 'admin', 'zone': 'greenroom', 'resource': 'file', 'operation': 'download'}

    expected = {
        'code': 200,
        'error_msg': '',
        'page': 0,
        'total': 1,
        'num_of_pages': 1,
        'result': {'has_permission': Like(True)},
    }

    headers = {'Content-Type': 'application/json'}

    pact.given('check has permission in auth service').upon_receiving('authorize in auth service').with_request(
        method='GET', path='/v1/' + test_has_permission_api, query=query, headers=headers
    ).will_respond_with(200, body=expected)
    from config import ConfigClass

    ConfigClass.AUTH_SERVICE = pact.uri + '/v1/'
    with pact:
        res = httpx.get(url=ConfigClass.AUTH_SERVICE + test_has_permission_api, params=query, headers=headers)

    assert res.status_code == 200
    pact.verify()
