# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import httpx

from config import ConfigClass


def data_ops_request(resource_key: str, operation: str, method: str) -> dict:
    url = ConfigClass.DATAOPS_SERVICE_v2 + 'resource/lock/'
    post_json = {'resource_key': resource_key, 'operation': operation}
    with httpx.Client(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
        response = client.request(url=url, method=method, json=post_json)
    if response.status_code != 200:
        raise Exception(f'resource {resource_key} already in used')

    return response.json()


def lock_resource(resource_key: str, operation: str) -> dict:
    return data_ops_request(resource_key, operation, 'POST')


def unlock_resource(resource_key: str, operation: str) -> dict:
    return data_ops_request(resource_key, operation, 'DELETE')
