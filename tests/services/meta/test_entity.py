# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from uuid import uuid4

import pytest

from app.components.exceptions import APIException
from config import ConfigClass
from models.models_item import ItemStatus
from services.meta import async_get_entity_by_id

MOCK_FILE_DATA = {
    'status': ItemStatus.ACTIVE,
    'container_code': 'test_project',
    'container_type': 'project',
    'created_time': '2021-05-10 19:43:55.382824',
    'extended': {'extra': {'attributes': {}, 'system_tags': [], 'tags': []}, 'id': str(uuid4())},
    'id': str(uuid4()),
    'last_updated_time': '2021-05-10 19:43:55.383021',
    'name': 'folder2',
    'owner': 'admin',
    'parent': str(uuid4()),
    'parent_path': 'test',
    'restore_path': None,
    'size': 0,
    'storage': {'id': str(uuid4()), 'location_uri': None, 'version': None},
    'type': 'folder',
    'zone': 1,
}


async def test_async_get_entity_by_id_200(httpx_mock):

    mock_data = {'result': MOCK_FILE_DATA}
    file_id = MOCK_FILE_DATA['id']
    httpx_mock.add_response(method='GET', url=f'{ConfigClass.METADATA_SERVICE}item/{file_id}/', json=mock_data)

    result = await async_get_entity_by_id(file_id)
    assert result == MOCK_FILE_DATA


async def test_async_get_entity_by_id_500(httpx_mock):
    mock_data = {'result': MOCK_FILE_DATA}
    file_id = MOCK_FILE_DATA['id']
    httpx_mock.add_response(
        method='GET', url=f'{ConfigClass.METADATA_SERVICE}item/{file_id}/', status_code=500, json=mock_data
    )

    with pytest.raises(APIException) as exc:
        await async_get_entity_by_id(file_id)

    expected_template_error_msg = 'Error calling Meta service get_node_by_id:'
    assert exc.value.status_code == 500
    assert expected_template_error_msg in exc.value.error_msg


async def test_async_get_entity_by_id_missing_entity(httpx_mock):
    mock_data = {'result': ''}
    file_id = MOCK_FILE_DATA['id']
    httpx_mock.add_response(method='GET', url=f'{ConfigClass.METADATA_SERVICE}item/{file_id}/', json=mock_data)

    with pytest.raises(APIException) as exc:
        await async_get_entity_by_id(file_id)

    expected_template_error_msg = 'Entity not found'
    assert expected_template_error_msg in exc.value.error_msg
