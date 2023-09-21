# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from uuid import uuid4

import pytest

from app.components.exceptions import APIException
from config import ConfigClass
from services.dataset import get_dataset_by_code
from services.dataset import get_dataset_by_id


async def test_get_dataset_by_id_success(httpx_mock):
    dataset_id = str(uuid4())
    result_data = {'name': 'fake'}
    httpx_mock.add_response(url=ConfigClass.DATASET_SERVICE + f'datasets/{dataset_id}', method='GET', json=result_data)
    result = await get_dataset_by_id(dataset_id)
    assert result == result_data


async def test_get_dataset_by_code_success(httpx_mock):
    code = 'test_project'
    result_data = {'name': 'fake'}
    httpx_mock.add_response(url=ConfigClass.DATASET_SERVICE + f'datasets/{code}', method='GET', json=result_data)
    result = await get_dataset_by_code(code)
    assert result == result_data


async def test_get_dataset_by_id_dataset_error_response(httpx_mock):
    dataset_id = str(uuid4())
    httpx_mock.add_response(
        url=ConfigClass.DATASET_SERVICE + f'datasets/{dataset_id}', method='GET', json={}, status_code=500
    )
    with pytest.raises(APIException):
        await get_dataset_by_id(dataset_id)


async def test_get_dataset_by_code_dataset_error_response(httpx_mock):
    code = 'test_project'
    httpx_mock.add_response(
        url=ConfigClass.DATASET_SERVICE + f'datasets/{code}', method='GET', json={}, status_code=500
    )
    with pytest.raises(APIException):
        await get_dataset_by_code(code)


async def test_get_dataset_by_id_dataset_not_found(httpx_mock):
    dataset_id = str(uuid4())
    httpx_mock.add_response(
        url=ConfigClass.DATASET_SERVICE + f'datasets/{dataset_id}', method='GET', json={}, status_code=200
    )
    with pytest.raises(APIException):
        await get_dataset_by_id(dataset_id)


async def test_get_dataset_by_code_dataset_not_found(httpx_mock):
    code = 'test_project'
    httpx_mock.add_response(
        url=ConfigClass.DATASET_SERVICE + f'datasets/{code}', method='GET', json={}, status_code=200
    )
    with pytest.raises(APIException):
        await get_dataset_by_code(code)
