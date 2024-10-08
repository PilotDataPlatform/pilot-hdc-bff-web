# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Any

import httpx
import requests
from httpx import Response

from app.components.exceptions import APIException
from config import ConfigClass
from models.api_response import EAPIResponseCode


async def async_get_entity_by_id(entity_id: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
        url = f'{ConfigClass.METADATA_SERVICE}item/{entity_id}/'
        response = await client.get(url)
    if response.status_code != 200:
        error_msg = f'Error calling Meta service get_node_by_id: {response.json()}'
        raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.internal_error.value)
    if not response.json()['result']:
        error_msg = 'Entity not found'
        raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.not_found.value)
    return response.json()['result']


def get_entity_by_id(entity_id: str) -> dict:
    response = requests.get(
        ConfigClass.METADATA_SERVICE + f'item/{entity_id}', timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT
    )
    if response.status_code != 200:
        error_msg = f'Error calling Meta service get_node_by_id: {response.json()}'
        raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.internal_error.value)
    if not response.json()['result']:
        error_msg = 'Entity not found'
        raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.not_found.value)
    return response.json()['result']


def get_entities_batch(entity_ids: list) -> list:
    response = requests.get(
        ConfigClass.METADATA_SERVICE + 'items/batch',
        params={'ids': entity_ids},
        timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT,
    )
    if response.status_code != 200:
        error_msg = f'Error calling Meta service get_node_by_id: {response.json()}'
        raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.internal_error.value)
    return response.json()['result']


async def search_entities(
    container_code: str,
    parent_path: str,
    zone: str,
    headers: dict,
    recursive: bool = False,
    name: str = '',
) -> list:
    payload = {
        'container_code': container_code,
        'parent_path': parent_path,
        'zone': zone,
        'recursive': recursive,
    }
    if name:
        payload['name'] = name
    response = requests.get(
        ConfigClass.METADATA_SERVICE + 'items/search',
        params=payload,
        headers=headers,
        timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT,
    )
    if response.status_code != 200:
        error_msg = f'Error calling Meta service search_entities: {response.json()}'
        raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.internal_error.value)
    return response.json()['result']


async def get_lineage_provenance(item_id: str) -> Response:
    """Get lineage and provenance for an item."""
    url = ConfigClass.METADATA_SERVICE + f'lineage/{item_id}/'
    async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
        return await client.get(url)
