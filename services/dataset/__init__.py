# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import httpx

from app.components.exceptions import APIException
from config import ConfigClass
from models.api_response import EAPIResponseCode


async def get_dataset_by_id(dataset_id: str) -> dict:
    async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
        response = await client.get(ConfigClass.DATASET_SERVICE + f'datasets/{dataset_id}')
    if response.status_code != 200:
        error_msg = f'Error calling Dataset service get_dataset_by_id: {response.json()}'
        raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.internal_error.value)
    if not response.json():
        error_msg = 'Dataset not found'
        raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.not_found.value)
    return response.json()


async def get_dataset_by_code(dataset_code: str) -> dict:
    async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
        response = await client.get(ConfigClass.DATASET_SERVICE + f'datasets/{dataset_code}')
    if response.status_code != 200:
        error_msg = f'Error calling Dataset service get_dataset_by_code: {response.json()}'
        raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.internal_error.value)
    if not response.json():
        error_msg = 'Dataset not found'
        raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.not_found.value)
    return response.json()
