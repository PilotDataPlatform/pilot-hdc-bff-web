# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import httpx
from pact import EachLike
from pact import Format
from pact import Like

test_list_events = 'events'


def test_get_user_invitation_should_return_200(pact_auth_service_init):
    pact = pact_auth_service_init

    query = {
        'project_code': 'contrattestproject',
        'page': '0',
        'page_size': '10',
        'order_type': 'asc',
        'order_by': 'timestamp',
    }

    expected = {
        'code': 200,
        'error_msg': '',
        'page': 0,
        'total': Like(10),
        'num_of_pages': Like(7),
        'result': EachLike(
            {
                'detail': Like({}),
                'event_type': Like('string'),
                'id': Format().uuid,
                'operator': Like('string'),
                'operator_id': Like('string'),
                'target_user': Like('string'),
                'target_user_id': Format().uuid,
                'timestamp': Like('string'),
            }
        ),
    }

    headers = {'Content-Type': 'application/json'}

    pact.given('get event list in auth service').upon_receiving('event in auth service').with_request(
        method='GET', path='/v1/' + test_list_events, query=query, headers=headers
    ).will_respond_with(200, body=expected)
    from config import ConfigClass

    ConfigClass.AUTH_SERVICE = pact.uri + '/v1/'
    with pact:
        res = httpx.get(url=ConfigClass.AUTH_SERVICE + test_list_events, params=query, headers=headers)

    assert res.status_code == 200
    pact.verify()
