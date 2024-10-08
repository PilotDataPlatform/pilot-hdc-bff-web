# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from uuid import UUID

import jwt
from fastapi import Request
from fastapi.datastructures import Headers

from app.auth import get_current_identity
from app.components.user.models import CurrentUser


async def test_get_current_identity_returns_user_object(fake, httpx_mock, settings):
    username = fake.user_name()
    user_id = fake.uuid4()
    user = {
        'id': user_id,
        'email': fake.email(),
        'first_name': fake.first_name(),
        'last_name': fake.last_name(),
        'role': 'member',
        'realm_roles': [],
        'attributes': {'status': 'active'},
    }

    token = jwt.encode({'preferred_username': username, 'sub': user_id}, key='')
    headers = Headers({'Authorization': token})
    request = Request(scope={'type': 'http', 'headers': headers.raw})

    url = f'{settings.AUTH_SERVICE}admin/user?username={username}&exact=true'
    httpx_mock.add_response(method='GET', url=url, json={'result': user})

    current_user = await get_current_identity(request)

    assert isinstance(current_user, CurrentUser)
    assert current_user.id == UUID(user_id)
    assert current_user.username == username
