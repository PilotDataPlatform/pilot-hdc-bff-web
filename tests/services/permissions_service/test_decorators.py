# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import json

import pytest
from fastapi import HTTPException
from fastapi import Request

from app.components.exceptions import APIException
from app.components.user.models import CurrentUser
from services.permissions_service.decorators import DatasetPermission
from services.permissions_service.decorators import find_project_code


async def test_find_project_code_returns_none_when_called_without_arguments():
    result = await find_project_code()

    assert result is None


async def test_find_project_code_raises_exception_when_called_with_both_project_code_and_project_id():
    with pytest.raises(HTTPException) as e:
        await find_project_code(project_code='code', project_id='id')

    assert 'mutually exclusive' in e.value.detail


async def test_find_project_code_returns_project_code_when_project_code_is_set(fake):
    project_code = fake.project_code()
    received_project_code = await find_project_code(project_code=project_code)

    assert received_project_code == project_code


async def test_find_project_code_returns_project_code_when_project_id_is_set(project_factory, project_service_client):
    project = project_factory.mock_retrieval_by_id()

    received_project_code = await find_project_code(
        project_id=str(project.id), project_service_client=project_service_client
    )

    assert received_project_code == project.code


async def test_dataset_permission_class_raises_exception_when_user_does_not_have_access_to_dataset(
    mocker, fake, dataset_factory, dataset_service_client, project_service_client
):
    dataset = dataset_factory.mock_retrieval_by_id()
    current_user = CurrentUser({'username': fake.user_name(), 'realm_roles': []})
    mocker.patch('services.permissions_service.decorators.get_current_identity', return_value=current_user)

    async def receive():
        return {'type': 'http.request', 'body': json.dumps({'dataset_id': str(dataset.id)}).encode()}

    request = Request(scope={'type': 'http', 'headers': []}, receive=receive)

    instance = DatasetPermission()

    with pytest.raises(APIException):
        await instance(
            request,
            dataset_service_client,
            project_service_client,
        )
