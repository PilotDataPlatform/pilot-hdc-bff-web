# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import re
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
    'name': 'jiang_folder_2',
    'owner': 'admin',
    'parent': str(uuid4()),
    'parent_path': 'test',
    'restore_path': None,
    'size': 0,
    'storage': {'id': str(uuid4()), 'location_uri': None, 'version': None},
    'type': 'folder',
    'zone': 1,
}


def test_list_meta_admin_200(test_client, httpx_mock, jwt_token_admin, has_permission_true):
    mock_data = {'result': [MOCK_FILE_DATA]}
    url = re.compile(ConfigClass.METADATA_SERVICE + 'items/search')
    httpx_mock.add_response(method='GET', url=url, json=mock_data)

    payload = {
        'zone': 'greenroom',
        'source_type': 'folder',
        'parent_path': MOCK_FILE_DATA['parent_path'],
        'project_code': 'test_project',
    }
    headers = {'Authorization': ''}
    response = test_client.get('v1/files/meta', params=payload, headers=headers)
    assert response.status_code == 200


def test_list_meta_contrib_200(test_client, httpx_mock, jwt_token_contrib, has_permission_true):
    url = re.compile(ConfigClass.METADATA_SERVICE + 'items/search')
    mock_data = {'result': [MOCK_FILE_DATA]}
    httpx_mock.add_response(method='GET', url=url, json=mock_data)

    payload = {
        'zone': 'core',
        'source_type': 'folder',
        'parent_path': MOCK_FILE_DATA['parent_path'],
        'project_code': 'test_project',
    }
    headers = {'Authorization': ''}
    response = test_client.get('v1/files/meta', params=payload, headers=headers)
    assert response.status_code == 200


def test_list_meta_wrong_project_403(test_client, httpx_mock, jwt_token_contrib):
    payload = {
        'zone': 'greenroom',
        'source_type': 'folder',
        'parent_path': MOCK_FILE_DATA['parent_path'],
        'project_code': 'wrong_project',
    }
    headers = {'Authorization': ''}
    response = test_client.get('v1/files/meta', params=payload, headers=headers)
    assert response.status_code == 403


def test_list_meta_contrib_permissions_subfolder_200(test_client, httpx_mock, jwt_token_contrib, has_permission_true):
    file_data = MOCK_FILE_DATA.copy()
    file_data['parent_path'] = 'admin'
    mock_data = {'result': [file_data]}
    url = re.compile(ConfigClass.METADATA_SERVICE + 'items/search')
    httpx_mock.add_response(method='GET', url=url, json=mock_data)

    payload = {'zone': 'core', 'source_type': 'folder', 'parent_path': 'test/folder1', 'project_code': 'test_project'}
    headers = {'Authorization': ''}
    response = test_client.get('v1/files/meta', params=payload, headers=headers)
    assert response.status_code == 200


def test_list_meta_bad_zone_400(test_client, httpx_mock, jwt_token_admin, has_permission_true):
    payload = {
        'zone': 'bad',
        'source_type': 'folder',
        'parent_path': MOCK_FILE_DATA['parent_path'],
        'project_code': 'test_project',
    }
    headers = {'Authorization': ''}
    response = test_client.get('v1/files/meta', params=payload, headers=headers)
    assert response.status_code == 400


def test_list_meta_bad_source_type_400(test_client, httpx_mock, jwt_token_admin, has_permission_true):
    payload = {
        'zone': 'greenroom',
        'source_type': 'bad',
        'parent_path': MOCK_FILE_DATA['parent_path'],
        'project_code': 'test_project',
    }
    headers = {'Authorization': ''}
    response = test_client.get('v1/files/meta', params=payload, headers=headers)
    assert response.status_code == 400


def test_list_meta_filter_200(test_client, httpx_mock, jwt_token_admin, has_permission_true):
    mock_data = {'result': [MOCK_FILE_DATA]}
    url = re.compile(ConfigClass.METADATA_SERVICE + 'items/search')
    httpx_mock.add_response(method='GET', url=url, json=mock_data)

    payload = {
        'zone': 'greenroom',
        'source_type': 'folder',
        'parent_path': MOCK_FILE_DATA['parent_path'],
        'project_code': 'test_project',
        'name': 'test%',
        'owner': 'test%',
    }
    headers = {'Authorization': ''}
    response = test_client.get('v1/files/meta', params=payload, headers=headers)
    assert response.status_code == 200


def test_list_meta_trash_200(test_client, httpx_mock, jwt_token_admin, has_permission_true):
    mock_data = {'result': [MOCK_FILE_DATA]}
    url = re.compile(ConfigClass.METADATA_SERVICE + 'items/search')
    httpx_mock.add_response(method='GET', url=url, json=mock_data)

    payload = {
        'zone': 'all',
        'source_type': 'trash',
        'parent_path': MOCK_FILE_DATA['parent_path'],
        'project_code': 'test_project',
    }
    headers = {'Authorization': ''}
    response = test_client.get('v1/files/meta', params=payload, headers=headers)
    assert response.status_code == 200


def test_list_meta_trash_contrib_200(test_client, httpx_mock, jwt_token_contrib, has_permission_true):
    mock_data = {'result': [MOCK_FILE_DATA]}
    url = re.compile(ConfigClass.METADATA_SERVICE + 'items/search')
    httpx_mock.add_response(method='GET', url=url, json=mock_data)

    payload = {
        'zone': 'all',
        'source_type': 'trash',
        'parent_path': MOCK_FILE_DATA['parent_path'],
        'project_code': 'test_project',
    }
    headers = {'Authorization': ''}
    response = test_client.get('v1/files/meta', params=payload, headers=headers)
    assert response.status_code == 200


def test_file_detail_bulk_200(test_client, requests_mocker, jwt_token_admin, has_permission_true):
    mock_data = {'result': [MOCK_FILE_DATA]}
    requests_mocker.get(ConfigClass.METADATA_SERVICE + 'items/batch', json=mock_data)

    payload = {'ids': [MOCK_FILE_DATA['id']]}
    headers = {'Authorization': ''}
    response = test_client.post('v1/files/bulk/detail', json=payload, headers=headers)
    assert response.status_code == 200


def test_file_detail_bulk_permissions_403(test_client, requests_mocker, jwt_token_contrib, has_permission_false):
    mock_data = {'result': [MOCK_FILE_DATA]}
    requests_mocker.get(ConfigClass.METADATA_SERVICE + 'items/batch', json=mock_data)

    payload = {'ids': [MOCK_FILE_DATA['id']]}
    headers = {'Authorization': ''}
    response = test_client.post('v1/files/bulk/detail', json=payload, headers=headers)
    assert response.status_code == 403
