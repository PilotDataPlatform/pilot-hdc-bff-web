# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import random

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
    response = await test_async_client.get('/v1/datasets/', headers=headers, params=params)

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
    response = await test_async_client.get('/v1/datasets/', headers=headers, params=params)

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
    """When current user has no admin role in the specified project code but has admin roles in other projects."""

    username = fake.user_name()
    project = project_factory.mock_retrieval_by_code()
    realm_roles = [
        f'{project.code}-{EUserRole.contributor.name}',
        f'{fake.project_code()}-{EUserRole.admin.name}',
    ]
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
    response = await test_async_client.get('/v1/datasets/', headers=headers, params=params)

    assert response.status_code == 200


async def test_list_datasets_with_project_code_parameter_replaces_it_with_project_id(
    mocker, test_async_client, httpx_mock, fake, project_factory
):
    """When current user has an admin role in the specified project code."""

    username = fake.user_name()
    project = project_factory.mock_retrieval_by_code()
    realm_roles = [f'{project.code}-{EUserRole.admin.name}']
    mocker.patch(
        'app.auth.get_current_identity', return_value=CurrentUser({'username': username, 'realm_roles': realm_roles})
    )
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.DATASET_SERVICE}datasets/?project_id={project.id}',
        json={},
    )

    headers = {'Authorization': ''}
    params = {'project_code': project.code}
    response = await test_async_client.get('/v1/datasets/', headers=headers, params=params)

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
    response = await test_async_client.get('/v1/datasets/', headers=headers, params=params)

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
    response = await test_async_client.get('/v1/datasets/', headers=headers, params=params)

    assert response.status_code == 200


async def test_list_datasets_returns_server_error_when_dataset_service_returns_unsuccessful_status_code_in_response(
    mocker, test_async_client, httpx_mock
):
    mocker.patch('app.auth.get_current_identity', return_value=CurrentUser({'username': 'admin', 'realm_roles': []}))
    headers = {'Authorization': ''}
    params = {'creator': 'any'}
    httpx_mock.add_response(method='GET', url=f'{ConfigClass.DATASET_SERVICE}datasets/?creator=admin', status_code=404)

    response = await test_async_client.get('/v1/datasets/', headers=headers, params=params)
    assert response.status_code == 500


async def test_list_dataset_version_sharing_requests_with_project_code_parameter_returns_200(
    mocker, test_async_client, httpx_mock, fake
):
    username = fake.user_name()
    project_code = fake.project_code()
    realm_roles = [f'{project_code}-{EUserRole.admin.name}']
    mocker.patch(
        'app.auth.get_current_identity', return_value=CurrentUser({'username': username, 'realm_roles': realm_roles})
    )
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.DATASET_SERVICE}version-sharing-requests/?project_code={project_code}',
        json={'result': []},
    )

    headers = {'Authorization': ''}
    params = {'project_code': project_code}
    response = await test_async_client.get('/v1/dataset-version-sharing-requests/', headers=headers, params=params)

    assert response.status_code == 200


async def test_list_dataset_version_sharing_requests_with_project_code_parameter_returns_forbidden(
    mocker, test_async_client, fake
):
    """When current user doesn't have admin role in the specified project code."""

    username = fake.user_name()
    project_code = fake.project_code()
    realm_roles = [f'{project_code}-{EUserRole.contributor.name}']
    mocker.patch(
        'app.auth.get_current_identity', return_value=CurrentUser({'username': username, 'realm_roles': realm_roles})
    )

    headers = {'Authorization': ''}
    params = {'project_code': project_code}
    response = await test_async_client.get('/v1/dataset-version-sharing-requests/', headers=headers, params=params)

    assert response.status_code == 403


async def test_create_dataset_version_sharing_request_returns_success(
    mocker, test_async_client, httpx_mock, fake, project_factory, dataset_factory
):
    dataset_version_id = fake.uuid4(cast_to=str)
    username = fake.user_name()
    target_project = project_factory.mock_retrieval_by_code()
    source_project = project_factory.mock_retrieval_by_id()
    dataset = dataset_factory.mock_retrieval_by_id(dataset_factory.generate(project_id=source_project.id))
    realm_roles = [f'{source_project.code}-{EUserRole.admin.name}']
    mocker.patch(
        'app.auth.get_current_identity', return_value=CurrentUser({'username': username, 'realm_roles': realm_roles})
    )
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.DATASET_SERVICE}dataset/versions/{dataset_version_id}',
        json={'dataset_id': str(dataset.id)},
    )
    httpx_mock.add_response(
        method='POST',
        url=f'{ConfigClass.DATASET_SERVICE}version-sharing-requests/',
        json={},
    )

    headers = {'Authorization': ''}
    body = {'version_id': dataset_version_id, 'project_code': target_project.code}
    response = await test_async_client.post('/v1/dataset-version-sharing-requests/', headers=headers, json=body)

    assert response.status_code == 200


async def test_create_dataset_version_sharing_request_returns_not_found_when_target_project_does_not_exist(
    mocker, test_async_client, httpx_mock, fake, project_factory, dataset_factory
):
    dataset_version_id = fake.uuid4(cast_to=str)
    username = fake.user_name()
    target_project_code = fake.project_code()
    realm_roles = [f'{fake.project_code()}-{EUserRole.admin.name}']
    mocker.patch(
        'app.auth.get_current_identity', return_value=CurrentUser({'username': username, 'realm_roles': realm_roles})
    )
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.PROJECT_SERVICE}/v1/projects/{target_project_code}',
        status_code=404,
    )

    headers = {'Authorization': ''}
    body = {'version_id': dataset_version_id, 'project_code': target_project_code}
    response = await test_async_client.post('/v1/dataset-version-sharing-requests/', headers=headers, json=body)

    assert response.status_code == 404
    assert response.json()['error_msg'] == 'Project not found'


async def test_create_dataset_version_sharing_request_returns_conflict_when_target_project_is_dataset_source_project(
    mocker, test_async_client, httpx_mock, fake, project_factory, dataset_factory
):
    dataset_version_id = fake.uuid4(cast_to=str)
    username = fake.user_name()
    target_project = project_factory.mock_retrieval_by_code()
    project_factory.mock_retrieval_by_id(target_project)
    dataset = dataset_factory.mock_retrieval_by_id(dataset_factory.generate(project_id=target_project.id))
    realm_roles = [f'{target_project.code}-{EUserRole.admin.name}']
    mocker.patch(
        'app.auth.get_current_identity', return_value=CurrentUser({'username': username, 'realm_roles': realm_roles})
    )
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.DATASET_SERVICE}dataset/versions/{dataset_version_id}',
        json={'dataset_id': str(dataset.id)},
    )

    headers = {'Authorization': ''}
    body = {'version_id': dataset_version_id, 'project_code': target_project.code}
    response = await test_async_client.post('/v1/dataset-version-sharing-requests/', headers=headers, json=body)

    assert response.status_code == 409
    assert response.json()['error_msg'] == 'Sharing is not permitted within the same project'


async def test_create_dataset_version_sharing_request_returns_forbidden_for_user_without_admin_role_in_source_project(
    mocker, test_async_client, httpx_mock, fake, project_factory, dataset_factory
):
    dataset_version_id = fake.uuid4(cast_to=str)
    username = fake.user_name()
    target_project = project_factory.mock_retrieval_by_code()
    source_project = project_factory.mock_retrieval_by_id()
    dataset = dataset_factory.mock_retrieval_by_id(dataset_factory.generate(project_id=source_project.id))
    realm_roles = [f'{target_project.code}-{EUserRole.admin.name}']
    mocker.patch(
        'app.auth.get_current_identity', return_value=CurrentUser({'username': username, 'realm_roles': realm_roles})
    )
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.DATASET_SERVICE}dataset/versions/{dataset_version_id}',
        json={'dataset_id': str(dataset.id)},
    )

    headers = {'Authorization': ''}
    body = {'version_id': dataset_version_id, 'project_code': target_project.code}
    response = await test_async_client.post('/v1/dataset-version-sharing-requests/', headers=headers, json=body)

    assert response.status_code == 403
    assert response.json()['error_msg'] == 'Permission denied'


async def test_update_dataset_version_sharing_request_with_declined_status_returns_success(
    mocker, test_async_client, httpx_mock, fake, project_factory
):
    version_sharing_request_id = fake.uuid4()
    username = fake.user_name()
    project = project_factory.mock_retrieval_by_id()
    realm_roles = [f'{project.code}-{EUserRole.admin.name}']
    mocker.patch(
        'app.auth.get_current_identity', return_value=CurrentUser({'username': username, 'realm_roles': realm_roles})
    )
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.DATASET_SERVICE}version-sharing-requests/{version_sharing_request_id}',
        json={'status': 'sent', 'project_code': project.code},
    )
    httpx_mock.add_response(
        method='PATCH',
        url=f'{ConfigClass.DATASET_SERVICE}version-sharing-requests/{version_sharing_request_id}',
        json={'source_project_id': str(project.id)},
    )

    headers = {'Authorization': ''}
    body = {'status': 'declined'}
    response = await test_async_client.patch(
        f'/v1/dataset-version-sharing-requests/{version_sharing_request_id}', headers=headers, json=body
    )

    assert response.status_code == 200


async def test_update_dataset_version_sharing_request_with_accepted_status_returns_success(
    mocker, test_async_client, httpx_mock, fake, project_factory
):
    version_sharing_request_id = fake.uuid4()
    username = fake.user_name()
    project = project_factory.mock_retrieval_by_id()
    realm_roles = [f'{project.code}-{EUserRole.admin.name}']
    mocker.patch(
        'app.auth.get_current_identity', return_value=CurrentUser({'username': username, 'realm_roles': realm_roles})
    )
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.DATASET_SERVICE}version-sharing-requests/{version_sharing_request_id}',
        json={'status': 'sent', 'project_code': project.code},
    )
    httpx_mock.add_response(
        method='PATCH',
        url=f'{ConfigClass.DATASET_SERVICE}version-sharing-requests/{version_sharing_request_id}',
        json={'source_project_id': str(project.id)},
    )
    httpx_mock.add_response(
        method='POST',
        url=f'{ConfigClass.DATASET_SERVICE}version-sharing-requests/{version_sharing_request_id}/start',
        status_code=204,
    )

    headers = {'Authorization': '', 'Session-Id': fake.uuid4()}
    body = {'status': 'accepted'}
    response = await test_async_client.patch(
        f'/v1/dataset-version-sharing-requests/{version_sharing_request_id}', headers=headers, json=body
    )

    assert response.status_code == 200


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


async def test_datasets_post_dataset_should_return_200(mocker, test_async_client, httpx_mock, project_factory):
    project = project_factory.mock_retrieval_by_code()
    realm_roles = [f'{project.code}-{EUserRole.contributor.name}']
    mocker.patch(
        'app.auth.get_current_identity', return_value=CurrentUser({'username': 'any', 'realm_roles': realm_roles})
    )

    headers = {'Authorization': ''}
    params = {'creator': 'any', 'project_code': project.code}
    httpx_mock.add_response(method='POST', url=f'{ConfigClass.DATASET_SERVICE}datasets/', status_code=200, json={})

    response = await test_async_client.post('/v1/datasets/', headers=headers, json=params)
    assert response.json() == {}
    assert response.status_code == 200


async def test_datasets_post_dataset_when_jwt_username_and_dataset_creator_are_different_should_return_403(
    mocker, test_async_client
):
    mocker.patch('app.auth.get_current_identity', return_value=CurrentUser({'username': 'any', 'realm_roles': []}))
    headers = {'Authorization': ''}
    params = {'creator': 'another'}

    response = await test_async_client.post('/v1/datasets/', headers=headers, json=params)
    assert response.status_code == 403


async def test_datasets_post_returns_forbidden_status_code_when_dataset_code_is_in_forbidden_list(
    mocker, test_async_client, settings
):
    mocker.patch('app.auth.get_current_identity', return_value=CurrentUser({'username': 'any'}))
    dataset_code = random.choice(list(settings.FORBIDDEN_CONTAINER_CODES))

    headers = {'Authorization': ''}
    response = await test_async_client.post('/v1/datasets/', headers=headers, json={'code': dataset_code})

    assert response.status_code == 403
    assert response.json()['error_msg'] == 'Dataset code is not allowed'


async def test_datasets_post_returns_forbidden_status_code_when_user_does_not_have_project_code_in_realm_roles(
    mocker, test_async_client, fake, settings
):
    mocker.patch('app.auth.get_current_identity', return_value=CurrentUser({'username': 'any', 'realm_roles': []}))
    dataset_code = fake.dataset_code()

    headers = {'Authorization': ''}
    response = await test_async_client.post('/v1/datasets/', headers=headers, json={'code': dataset_code})

    assert response.status_code == 403
    assert response.json()['error_msg'] == 'Project code is not allowed'


async def test_dataset_get_version_should_build_correct_url(mocker, test_async_client, httpx_mock, dataset_factory):
    dataset = dataset_factory.mock_retrieval_by_id()
    current_user = CurrentUser({'username': dataset.creator})
    mocker.patch('app.auth.get_current_identity', return_value=current_user)
    mocker.patch('services.permissions_service.decorators.get_current_identity', return_value=current_user)

    headers = {'Authorization': ''}
    params = {'order_by': 'asc'}
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.DATASET_SERVICE}dataset/versions?order_by=asc&dataset_id={dataset.id}',
        status_code=200,
        json={},
    )

    response = await test_async_client.get(f'/v1/dataset/{dataset.id}/versions', headers=headers, params=params)
    assert response.json() == {}
    assert response.status_code == 200
