# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import copy
from urllib import parse
from uuid import uuid4

from config import ConfigClass
from models.models_item import ItemStatus

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

MOCK_FILE_DATA_2 = {
    'status': ItemStatus.ACTIVE,
    'container_code': 'test_project',
    'container_type': 'project',
    'created_time': '2021-05-10 19:43:55.382824',
    'extended': {'extra': {'attributes': {}, 'system_tags': [], 'tags': []}, 'id': str(uuid4())},
    'id': str(uuid4()),
    'last_updated_time': '2021-05-10 19:43:55.383021',
    'name': 'new_file.txt',
    'owner': 'admin',
    'parent': str(uuid4()),
    'parent_path': 'test',
    'restore_path': None,
    'size': 0,
    'storage': {'id': str(uuid4()), 'location_uri': None, 'version': None},
    'type': 'file',
    'zone': 1,
}

template_id = '3f73f4d4-82e7-4269-8d2e-3c8c678a6b05'

MOCK_TEMPLATE_DATA = {
    'id': template_id,
    'name': 'Template01',
    'project_code': 'test_project',
    'attributes': [
        {
            'name': 'attr1',
            'optional': True,
            'type': 'multiple_choice',
            'options': ['A', 'B', 'C'],
            'manifest_id': template_id,
        }
    ],
}


async def test_list_templates_admin_200(test_async_client, httpx_mock, jwt_token_admin):

    mock_data = {'result': [MOCK_TEMPLATE_DATA]}
    url = f"{ConfigClass.METADATA_SERVICE}template/?project_code={MOCK_TEMPLATE_DATA['project_code']}"
    httpx_mock.add_response(
        method='GET',
        url=url,
        status_code=200,
        json=mock_data,
    )

    params = {'project_code': 'test_project'}
    headers = {'Authorization': ''}
    response = await test_async_client.get('/v1/data/manifests', query_string=params, headers=headers)
    assert response.status_code == 200


async def test_create_new_templates_admin_200(test_async_client, httpx_mock, jwt_token_admin, has_permission_true):
    mock_data = {'result': [MOCK_TEMPLATE_DATA]}
    httpx_mock.add_response(
        method='POST',
        url=ConfigClass.METADATA_SERVICE + 'template/',
        status_code=200,
        json=mock_data,
    )

    headers = {'Authorization': ''}
    response = await test_async_client.post('/v1/data/manifests', json=MOCK_TEMPLATE_DATA, headers=headers)
    assert response.status_code == 200


async def test_get_template_by_id_admin_200(test_async_client, httpx_mock, jwt_token_admin):

    mock_data = {'result': MOCK_TEMPLATE_DATA}
    httpx_mock.add_response(
        method='GET',
        url=ConfigClass.METADATA_SERVICE + f'template/{template_id}/',
        json=mock_data,
    )

    headers = {'Authorization': ''}
    response = await test_async_client.get(f'/v1/data/manifest/{template_id}', headers=headers)
    assert response.status_code == 200


async def test_get_template_by_invalid_id_admin_404(test_async_client, httpx_mock, jwt_token_admin):
    invalid_id = '1234'

    mock_data = {'result': {}}
    httpx_mock.add_response(method='GET', url=ConfigClass.METADATA_SERVICE + f'template/{invalid_id}/', json=mock_data)

    headers = {'Authorization': ''}
    response = await test_async_client.get(f'/v1/data/manifest/{invalid_id}', headers=headers)
    assert response.status_code == 404


async def test_update_template_attributes_admin_200(
    test_async_client, httpx_mock, jwt_token_admin, has_permission_true
):
    MOCK_TEMPLATE_UPDATE = copy.deepcopy(MOCK_TEMPLATE_DATA)
    MOCK_TEMPLATE_UPDATE['attributes'][0]['name'] = 'attr2'

    mock_data_1 = {'result': MOCK_TEMPLATE_DATA}

    mock_data_2 = {'result': [MOCK_TEMPLATE_UPDATE]}

    httpx_mock.add_response(
        method='GET', url=ConfigClass.METADATA_SERVICE + f'template/{template_id}/', json=mock_data_1
    )
    httpx_mock.add_response(
        method='PUT', url=ConfigClass.METADATA_SERVICE + f'template/?id={template_id}', json=mock_data_2
    )

    headers = {'Authorization': ''}
    response = await test_async_client.put(
        f'/v1/data/manifest/{template_id}', json=MOCK_TEMPLATE_UPDATE, headers=headers
    )
    assert response.status_code == 200


async def test_update_template_attributes_permission_denied_403(
    test_async_client, jwt_token_contrib, has_permission_false
):
    MOCK_TEMPLATE_UPDATE = copy.deepcopy(MOCK_TEMPLATE_DATA)
    MOCK_TEMPLATE_UPDATE['attributes'][0]['name'] = 'attr2'

    headers = {'Authorization': ''}
    response = await test_async_client.put(
        f'/v1/data/manifest/{template_id}', json=MOCK_TEMPLATE_UPDATE, headers=headers
    )
    assert response.status_code == 403


async def test_delete_template_by_id_admin_200(test_async_client, httpx_mock, jwt_token_admin, has_permission_true):
    mock_data_template = {'result': MOCK_TEMPLATE_DATA}

    mock_data = {'result': []}

    httpx_mock.add_response(
        method='GET', url=ConfigClass.METADATA_SERVICE + f'template/{template_id}/', json=mock_data_template
    )
    for zone in [0, 1]:
        for status in [ItemStatus.ACTIVE, ItemStatus.ARCHIVED]:
            url = (
                f'{ConfigClass.METADATA_SERVICE}items/search/'
                f'?container_code=test_project&zone={zone}&recursive=true&status={status}&type=file'
            )
            httpx_mock.add_response(method='GET', url=url, json=mock_data)

    httpx_mock.add_response(
        method='DELETE', url=ConfigClass.METADATA_SERVICE + f'template/?id={template_id}', json=mock_data
    )

    headers = {'Authorization': ''}
    response = await test_async_client.delete(f'/v1/data/manifest/{template_id}', headers=headers)
    assert response.status_code == 200


async def test_delete_template_by_id_permission_denied_403(
    test_async_client,
    httpx_mock,
    jwt_token_contrib,
    has_permission_false,
):

    mock_data = {'result': MOCK_TEMPLATE_DATA}
    httpx_mock.add_response(method='GET', url=f'{ConfigClass.METADATA_SERVICE}template/{template_id}/', json=mock_data)

    headers = {'Authorization': ''}
    response = await test_async_client.delete(f'/v1/data/manifest/{template_id}', headers=headers)
    assert response.status_code == 403


async def test_update_template_attributes_of_file_admin_200(
    test_async_client, httpx_mock, jwt_token_admin, has_permission_true
):
    MOCK_FILE_DATA_ATTR = copy.deepcopy(MOCK_FILE_DATA)
    MOCK_FILE_DATA_ATTR['extended']['extra']['attributes'] = {template_id: {'attr1': 'B'}}
    mock_data = {'result': MOCK_FILE_DATA_ATTR}
    file_id = MOCK_FILE_DATA_ATTR['id']
    httpx_mock.add_response(method='GET', url=f'{ConfigClass.METADATA_SERVICE}item/{file_id}/', json=mock_data)

    mock_data = {'result': MOCK_FILE_DATA_ATTR}
    httpx_mock.add_response(method='PUT', url=f'{ConfigClass.METADATA_SERVICE}item/?id={file_id}', json=mock_data)

    headers = {'Authorization': ''}
    response = await test_async_client.put(
        f'/v1/file/{file_id}/manifest', json={'attr1': 'B', 'project_code': 'test_project'}, headers=headers
    )
    assert response.status_code == 200


async def test_update_template_attributes_of_file_permission_denied_contrib_403(
    test_async_client, httpx_mock, jwt_token_contrib, has_permission_false
):
    MOCK_FILE_DATA_ATTR = copy.deepcopy(MOCK_FILE_DATA)
    MOCK_FILE_DATA_ATTR['extended']['extra']['attributes'] = {template_id: {'attr1': 'C'}}
    mock_data = {'result': MOCK_FILE_DATA_ATTR}
    file_id = MOCK_FILE_DATA_ATTR['id']
    httpx_mock.add_response(method='GET', url=f'{ConfigClass.METADATA_SERVICE}item/{file_id}/', json=mock_data)

    headers = {'Authorization': ''}
    response = await test_async_client.put(
        f'/v1/file/{file_id}/manifest', json={'attr1': 'B', 'project_code': 'test_project'}, headers=headers
    )
    assert response.status_code == 403


async def test_update_template_attributes_of_file_permission_denied_admin_403(
    test_async_client, httpx_mock, jwt_token_admin, has_permission_false
):
    MOCK_FILE_DATA_ATTR = copy.deepcopy(MOCK_FILE_DATA)
    MOCK_FILE_DATA_ATTR['extended']['extra']['attributes'] = {template_id: {'attr1': 'C'}}
    mock_data = {'result': MOCK_FILE_DATA_ATTR}
    file_id = MOCK_FILE_DATA_ATTR['id']
    httpx_mock.add_response(method='GET', url=f'{ConfigClass.METADATA_SERVICE}item/{file_id}/', json=mock_data)

    headers = {'Authorization': ''}
    response = await test_async_client.put(
        f'/v1/file/{file_id}/manifest', json={'attr1': 'B', 'project_code': 'test_project'}, headers=headers
    )
    assert response.status_code == 403


async def test_import_template_admin_200(test_async_client, httpx_mock, jwt_token_admin, has_permission_true):

    mock_data = {'result': [MOCK_TEMPLATE_DATA]}
    httpx_mock.add_response(method='POST', url=f'{ConfigClass.METADATA_SERVICE}template/', json=mock_data)

    headers = {'Authorization': ''}
    response = await test_async_client.post('/v1/import/manifest', json=MOCK_TEMPLATE_DATA, headers=headers)
    assert response.status_code == 200


async def test_list_file_template_attributes_admin_200(
    test_async_client, httpx_mock, jwt_token_admin, has_permission_true
):
    MOCK_FILE_DATA_ATTR = copy.deepcopy(MOCK_FILE_DATA)
    MOCK_FILE_DATA_ATTR['extended']['extra']['attributes'] = {template_id: {'attr1': 'A'}}
    file_id = MOCK_FILE_DATA['id']

    mock_data = {'result': MOCK_FILE_DATA_ATTR}
    httpx_mock.add_response(method='GET', url=f'{ConfigClass.METADATA_SERVICE}item/{file_id}/', json=mock_data)

    mock_data = {'result': MOCK_TEMPLATE_DATA}
    url = f'{ConfigClass.METADATA_SERVICE}template/{template_id}/'
    httpx_mock.add_response(method='GET', url=url, json=mock_data)

    headers = {'Authorization': ''}
    payload = {'geid_list': [file_id], 'project_code': 'test_project'}
    response = await test_async_client.post('/v1/file/manifest/query', json=payload, headers=headers)
    assert response.status_code == 200


async def test_list_file_template_attributes_permission_denied_contrib_403(
    test_async_client, httpx_mock, jwt_token_contrib, has_permission_false
):
    MOCK_FILE_DATA_ATTR = copy.deepcopy(MOCK_FILE_DATA)
    MOCK_FILE_DATA_ATTR['extended']['extra']['attributes'] = {template_id: {'attr1': 'A'}}
    file_id = MOCK_FILE_DATA['id']

    mock_data = {'result': MOCK_FILE_DATA_ATTR}
    httpx_mock.add_response(method='GET', url=f'{ConfigClass.METADATA_SERVICE}item/{file_id}/', json=mock_data)

    headers = {'Authorization': ''}
    payload = {'geid_list': [file_id]}
    response = await test_async_client.post('/v1/file/manifest/query', json=payload, headers=headers)
    assert response.status_code == 403


async def test_list_file_template_attributes_template_not_found_contrib_404(
    test_async_client, httpx_mock, jwt_token_contrib, has_permission_true
):
    MOCK_FILE_DATA_ATTR = copy.deepcopy(MOCK_FILE_DATA)
    MOCK_FILE_DATA_ATTR['extended']['extra']['attributes'] = {template_id: {'attr1': 'A'}}
    file_id = MOCK_FILE_DATA_ATTR['id']

    mock_data = {'result': MOCK_FILE_DATA_ATTR}
    httpx_mock.add_response(method='GET', url=f'{ConfigClass.METADATA_SERVICE}item/{file_id}/', json=mock_data)

    mock_data = {}
    url = f'{ConfigClass.METADATA_SERVICE}template/{template_id}/'
    httpx_mock.add_response(method='GET', url=url, json=mock_data, status_code=404)

    headers = {'Authorization': ''}
    payload = {'geid_list': [file_id], 'project_code': 'test_project'}
    response = await test_async_client.post('/v1/file/manifest/query', json=payload, headers=headers)
    assert response.status_code == 404


async def test_attach_attributes_to_file_contrib_missing_attributes_field_400(test_async_client, jwt_token_contrib):
    headers = {'Authorization': ''}
    payload = {
        'item_ids': [MOCK_FILE_DATA['id']],
        'manifest_id': template_id,
        'project_code': MOCK_FILE_DATA['container_code'],
    }
    response = await test_async_client.post('/v1/file/attributes/attach', json=payload, headers=headers)
    assert response.status_code == 400


async def test_attach_attributes_to_file_contrib_invalid_role_field_403(test_async_client, jwt_token_contrib):

    headers = {'Authorization': ''}
    payload = {
        'item_ids': [MOCK_FILE_DATA['id']],
        'manifest_id': template_id,
        'project_code': MOCK_FILE_DATA['container_code'],
        'attributes': {'attr1': 'A'},
    }

    response = await test_async_client.post('/v1/file/attributes/attach', json=payload, headers=headers)
    assert response.status_code == 403


async def test_attach_attributes_to_folder_contrib_subfolder_200(
    test_async_client, httpx_mock, jwt_token_contrib, has_permission_true
):
    mock_file = copy.deepcopy(MOCK_FILE_DATA)
    mock_file['parent_path'] = 'test/folder2'
    mock_file['type'] = 'file'

    file_id = mock_file['id']
    mock_entity = {'result': MOCK_FILE_DATA}
    httpx_mock.add_response(method='GET', url=f'{ConfigClass.METADATA_SERVICE}item/{file_id}/', json=mock_entity)

    mock_search = {'result': [MOCK_FILE_DATA]}
    url_parent_path = parse.quote_plus(mock_file['parent_path'])
    url = (
        f'{ConfigClass.METADATA_SERVICE}items/search/'
        f"?container_code={mock_file['container_code']}"
        f"&zone={mock_file['zone']}&recursive=true"
        f"&status={mock_file['status']}&type={mock_file['type']}"
        f"&owner={mock_file['owner']}&parent_path={url_parent_path}"
    )
    httpx_mock.add_response(method='GET', url=url, json=mock_search)

    MOCK_FILE_DATA_ATTR = copy.deepcopy(MOCK_FILE_DATA)
    MOCK_FILE_DATA_ATTR['extended']['extra']['attributes'] = {template_id: {'attr1': 'A'}}
    mock_batch = {'result': [MOCK_FILE_DATA_ATTR]}
    url = f"{ConfigClass.METADATA_SERVICE}items/batch/?ids={MOCK_FILE_DATA_ATTR['id']}"
    httpx_mock.add_response(method='PUT', url=url, json=mock_batch)

    headers = {'Authorization': ''}
    payload = {
        'item_ids': [MOCK_FILE_DATA['id']],
        'manifest_id': template_id,
        'project_code': MOCK_FILE_DATA['container_code'],
        'attributes': {'attr1': 'A'},
    }
    response = await test_async_client.post('/v1/file/attributes/attach', json=payload, headers=headers)
    assert response.status_code == 200


async def test_attach_attributes_to_folder_contrib_403(
    test_async_client, httpx_mock, jwt_token_contrib, has_permission_false
):
    mock_file = copy.deepcopy(MOCK_FILE_DATA)
    mock_file['parent_path'] = 'admin/folder1'

    file_id = mock_file['id']
    mock_data = {'result': mock_file}
    httpx_mock.add_response(method='GET', url=f'{ConfigClass.METADATA_SERVICE}item/{file_id}/', json=mock_data)

    headers = {'Authorization': ''}
    payload = {
        'item_ids': [mock_file['id']],
        'manifest_id': template_id,
        'project_code': mock_file['container_code'],
        'attributes': {'attr1': 'A'},
    }
    response = await test_async_client.post('/v1/file/attributes/attach', json=payload, headers=headers)
    assert response.status_code == 403


async def test_attach_attributes_to_folder_failed_folder_search_contrib_500(
    test_async_client, httpx_mock, jwt_token_contrib, has_permission_true
):
    mock_file = copy.deepcopy(MOCK_FILE_DATA)
    mock_file['parent_path'] = 'test/folder2'
    mock_file['type'] = 'file'

    file_id = mock_file['id']
    mock_entity = {'result': MOCK_FILE_DATA}
    httpx_mock.add_response(method='GET', url=f'{ConfigClass.METADATA_SERVICE}item/{file_id}/', json=mock_entity)

    mock_search = {'result': []}
    url_parent_path = parse.quote_plus(mock_file['parent_path'])
    url = (
        f'{ConfigClass.METADATA_SERVICE}items/search/'
        f"?container_code={mock_file['container_code']}"
        f"&zone={mock_file['zone']}&recursive=true"
        f"&status={mock_file['status']}&type={mock_file['type']}"
        f"&owner={mock_file['owner']}&parent_path={url_parent_path}"
    )
    httpx_mock.add_response(method='GET', url=url, status_code=500, json=mock_search)

    headers = {'Authorization': ''}
    payload = {
        'item_ids': [mock_file['id']],
        'manifest_id': template_id,
        'project_code': mock_file['container_code'],
        'attributes': {'attr1': 'A'},
    }
    response = await test_async_client.post('/v1/file/attributes/attach', json=payload, headers=headers)
    assert response.status_code == 500


async def test_attach_attributes_to_file_and_folder_contrib_200(
    test_async_client, httpx_mock, jwt_token_contrib, has_permission_true
):
    MOCK_FILE_DATA_ATTR_1 = copy.deepcopy(MOCK_FILE_DATA)
    MOCK_FILE_DATA_ATTR_2 = copy.deepcopy(MOCK_FILE_DATA_2)

    file_id_1 = MOCK_FILE_DATA_ATTR_1['id']
    mock_data_folder = {'result': MOCK_FILE_DATA_ATTR_1}
    file_id_2 = MOCK_FILE_DATA_ATTR_2['id']
    mock_data_file = {'result': MOCK_FILE_DATA_ATTR_2}

    httpx_mock.add_response(method='GET', url=f'{ConfigClass.METADATA_SERVICE}item/{file_id_1}/', json=mock_data_folder)
    httpx_mock.add_response(method='GET', url=f'{ConfigClass.METADATA_SERVICE}item/{file_id_2}/', json=mock_data_file)

    mock_data = {'result': [MOCK_FILE_DATA_ATTR_1]}
    url_parent_path = parse.quote_plus(f"{MOCK_FILE_DATA_ATTR_1['parent_path']}/{MOCK_FILE_DATA_ATTR_1['name']}")
    url_1 = (
        f'{ConfigClass.METADATA_SERVICE}items/search/'
        f"?container_code={MOCK_FILE_DATA_ATTR_1['container_code']}"
        f"&zone={MOCK_FILE_DATA_ATTR_1['zone']}&recursive=true"
        f"&status={MOCK_FILE_DATA_ATTR_1['status']}&type=file"
        f"&owner={MOCK_FILE_DATA_ATTR_1['owner']}&parent_path={url_parent_path}"
    )
    httpx_mock.add_response(method='GET', url=url_1, json=mock_data)

    MOCK_FILE_DATA_ATTR_1['extended']['extra']['attributes'] = {template_id: {'attr1': 'A'}}

    MOCK_FILE_DATA_ATTR_2['extended']['extra']['attributes'] = {template_id: {'attr1': 'A'}}

    mock_data = {'result': [MOCK_FILE_DATA_ATTR_1, MOCK_FILE_DATA_ATTR_2]}
    url = (
        f'{ConfigClass.METADATA_SERVICE}items/batch/?'
        f"ids={MOCK_FILE_DATA_ATTR_1['id']}&ids={MOCK_FILE_DATA_ATTR_2['id']}"
    )
    httpx_mock.add_response(method='PUT', url=url, json=mock_data)

    headers = {'Authorization': ''}
    payload = {
        'item_ids': [MOCK_FILE_DATA['id'], MOCK_FILE_DATA_2['id']],
        'manifest_id': template_id,
        'project_code': MOCK_FILE_DATA['container_code'],
        'attributes': {'attr1': 'A'},
    }
    response = await test_async_client.post('/v1/file/attributes/attach', json=payload, headers=headers)
    assert response.status_code == 200
