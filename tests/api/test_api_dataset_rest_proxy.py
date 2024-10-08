# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from uuid import uuid4

from app.components.user.models import CurrentUser
from config import ConfigClass
from models.user_type import EUserRole


async def test_list_datasets_with_creator_parameter_returns_200(mocker, test_async_client, httpx_mock):
    mocker.patch('app.auth.get_current_identity', return_value=CurrentUser({'username': 'any', 'realm_roles': []}))
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.DATASET_SERVICE}datasets/?creator=any',
        json={},
    )

    headers = {'Authorization': ''}
    params = {'creator': 'any'}
    response = await test_async_client.get('/v1/datasets/', headers=headers, query_string=params)

    assert response.status_code == 200


async def test_list_datasets_with_creator_parameter_replaces_creator_value_with_current_identity(
    mocker, test_async_client, httpx_mock, fake
):
    username = fake.user_name()
    mocker.patch('app.auth.get_current_identity', return_value=CurrentUser({'username': username, 'realm_roles': []}))
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.DATASET_SERVICE}datasets/?creator={username}',
        json={},
    )

    headers = {'Authorization': ''}
    params = {'creator': fake.user_name()}
    response = await test_async_client.get('/v1/datasets/', headers=headers, query_string=params)

    assert response.status_code == 200


async def test_list_datasets_without_creator_parameter_adds_project_id_any_and_or_creator_parameters(
    mocker, test_async_client, httpx_mock, fake, project_factory
):
    """When current user has the project admin role in any project."""

    username = fake.user_name()
    project_1 = project_factory.mock_retrieval_by_code()
    project_2 = project_factory.mock_retrieval_by_code()
    realm_roles = [
        f'{fake.project_code()}-{EUserRole.contributor.name}',
        f'{fake.project_code()}-{EUserRole.collaborator.name}',
        f'{project_1.code}-{EUserRole.admin.name}',
        f'{project_2.code}-{EUserRole.admin.name}',
    ]
    mocker.patch(
        'app.auth.get_current_identity', return_value=CurrentUser({'username': username, 'realm_roles': realm_roles})
    )
    httpx_mock.add_response(
        method='GET',
        url=(
            f'{ConfigClass.DATASET_SERVICE}datasets/?'
            f'project_id_any={project_1.id},{project_2.id}&or_creator={username}'
        ),
        json={},
    )

    headers = {'Authorization': ''}
    response = await test_async_client.get('/v1/datasets/', headers=headers)

    assert response.status_code == 200


async def test_list_datasets_without_creator_parameter_adds_only_creator_parameter(
    mocker, test_async_client, httpx_mock, fake
):
    """When current user doesn't have the project admin role in any project."""

    username = fake.user_name()
    realm_roles = [f'{fake.project_code()}-{EUserRole.contributor.name}']
    mocker.patch(
        'app.auth.get_current_identity', return_value=CurrentUser({'username': username, 'realm_roles': realm_roles})
    )
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.DATASET_SERVICE}datasets/?creator={username}',
        json={},
    )

    headers = {'Authorization': ''}
    response = await test_async_client.get('/v1/datasets/', headers=headers)

    assert response.status_code == 200


async def test_list_datasets_with_project_code_parameter_replaces_it_with_project_id_and_adds_creator_parameter(
    mocker, test_async_client, httpx_mock, fake, project_factory
):
    """When current user has no admin role in the specified project code."""

    username = fake.user_name()
    project = project_factory.mock_retrieval_by_code()
    realm_roles = [f'{project.code}-{EUserRole.contributor.name}']
    mocker.patch(
        'app.auth.get_current_identity', return_value=CurrentUser({'username': username, 'realm_roles': realm_roles})
    )
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.DATASET_SERVICE}datasets/?creator={username}&project_id={project.id}',
        json={},
    )

    headers = {'Authorization': ''}
    params = {'project_code': project.code}
    response = await test_async_client.get('/v1/datasets/', headers=headers, query_string=params)

    assert response.status_code == 200


async def test_list_datasets_with_project_code_parameter_returns_forbidden(mocker, test_async_client, fake):
    """When current user doesn't have any roles in the specified project code."""

    username = fake.user_name()
    realm_roles = [f'{fake.project_code()}-{EUserRole.admin.name}']
    mocker.patch(
        'app.auth.get_current_identity', return_value=CurrentUser({'username': username, 'realm_roles': realm_roles})
    )

    headers = {'Authorization': ''}
    params = {'project_code': fake.project_code()}
    response = await test_async_client.get('/v1/datasets/', headers=headers, query_string=params)

    assert response.status_code == 403


async def test_list_datasets_with_project_code_and_creator_parameters_replaces_project_code_with_project_id_parameter(
    mocker, test_async_client, httpx_mock, fake, project_factory
):
    username = fake.user_name()
    project = project_factory.mock_retrieval_by_code()
    realm_roles = [f'{project.code}-{EUserRole.contributor.name}']
    mocker.patch(
        'app.auth.get_current_identity', return_value=CurrentUser({'username': username, 'realm_roles': realm_roles})
    )
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.DATASET_SERVICE}datasets/?creator={username}&project_id={project.id}',
        json={},
    )

    headers = {'Authorization': ''}
    params = {'creator': username, 'project_code': project.code}
    response = await test_async_client.get('/v1/datasets/', headers=headers, query_string=params)

    assert response.status_code == 200


async def test_list_datasets_returns_server_error_when_dataset_service_returns_unsuccessful_status_code_in_response(
    mocker, test_async_client, httpx_mock
):
    mocker.patch('app.auth.get_current_identity', return_value=CurrentUser({'username': 'admin', 'realm_roles': []}))
    headers = {'Authorization': ''}
    params = {'creator': 'any'}
    httpx_mock.add_response(method='GET', url=f'{ConfigClass.DATASET_SERVICE}datasets/?creator=admin', status_code=404)

    response = await test_async_client.get('/v1/datasets/', headers=headers, query_string=params)
    assert response.status_code == 500


async def test_datasets_get_dataset_by_identifier_should_return_200(
    mocker, test_async_client, httpx_mock, dataset_factory
):
    dataset = dataset_factory.mock_retrieval_by_id()
    mocker.patch('app.auth.get_current_identity', return_value=CurrentUser({'username': dataset.creator}))

    headers = {'Authorization': ''}
    response = await test_async_client.get(f'/v1/datasets/{dataset.id}', headers=headers)

    assert response.status_code == 200


async def test_datasets_get_dataset_by_id_returns_200_when_user_is_not_creator_but_has_admin_role(
    fake, mocker, test_async_client, project_factory, dataset_factory
):
    username = fake.user_name()
    project = project_factory.mock_retrieval_by_code()
    dataset = dataset_factory.generate(project_id=project.id)
    dataset_factory.mock_retrieval_by_id(dataset)
    realm_roles = [f'{project.code}-{EUserRole.admin.name}']
    mocker.patch(
        'app.auth.get_current_identity', return_value=CurrentUser({'username': username, 'realm_roles': realm_roles})
    )

    headers = {'Authorization': ''}
    response = await test_async_client.get(f'/v1/datasets/{dataset.id}', headers=headers)
    assert response.status_code == 200


async def test_datasets_get_dataset_by_identifier_should_return_409_when_current_identity_dont_match(
    mocker, test_async_client, httpx_mock
):
    mocker.patch('app.auth.get_current_identity', return_value=CurrentUser({'username': 'admin'}))
    headers = {'Authorization': ''}
    httpx_mock.add_response(
        method='GET', url=f'{ConfigClass.DATASET_SERVICE}datasets/identifier', status_code=200, json={'creator': 'any'}
    )

    response = await test_async_client.get('/v1/datasets/identifier', headers=headers)
    assert response.status_code == 403
    assert response.json() == {'code': 403, 'error_msg': 'Permission denied', 'result': ''}


async def test_datasets_get_dataset_by_identifier_should_return_dataset_service_response(
    mocker, test_async_client, httpx_mock
):
    mocker.patch('app.auth.get_current_identity', return_value=CurrentUser({'username': 'admin'}))
    headers = {'Authorization': ''}
    httpx_mock.add_response(
        method='GET', url=f'{ConfigClass.DATASET_SERVICE}datasets/identifier', status_code=500, json={'error': 'any'}
    )

    response = await test_async_client.get('/v1/datasets/identifier', headers=headers)
    assert response.status_code == 500
    assert response.json() == {'error': 'any'}


async def test_datasets_post_dataset_should_return_200(mocker, test_async_client, httpx_mock):
    mocker.patch('app.auth.get_current_identity', return_value=CurrentUser({'username': 'any'}))
    headers = {'Authorization': ''}
    params = {'creator': 'any'}
    httpx_mock.add_response(method='POST', url=f'{ConfigClass.DATASET_SERVICE}datasets/', status_code=200, json={})

    response = await test_async_client.post('/v1/datasets/', headers=headers, json=params)
    assert response.json() == {}
    assert response.status_code == 200


async def test_datasets_post_dataset_when_jwt_username_and_dataset_creator_are_different_should_return_403(
    mocker, test_async_client, httpx_mock
):
    mocker.patch('app.auth.get_current_identity', return_value=CurrentUser({'username': 'any'}))
    headers = {'Authorization': ''}
    params = {'creator': 'another'}

    response = await test_async_client.post('/v1/datasets/', headers=headers, json=params)
    assert response.status_code == 403


async def test_dataset_get_version_should_build_correct_url(mocker, test_async_client, httpx_mock):
    mocker.patch('app.auth.get_current_identity', return_value=CurrentUser({'username': 'any'}))
    headers = {'Authorization': ''}
    params = {'order_by': 'asc'}
    dataset_id = str(uuid4())
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.DATASET_SERVICE}dataset/versions?order_by=asc&dataset_id={dataset_id}',
        status_code=200,
        json={},
    )

    response = await test_async_client.get(f'/v1/dataset/{dataset_id}/versions', headers=headers, query_string=params)
    assert response.json() == {}
    assert response.status_code == 200
