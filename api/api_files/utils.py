# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import requests

from app.components.exceptions import APIException
from config import ConfigClass
from models.api_response import EAPIResponseCode


def get_collection_by_id(collection_geid):
    url = f'{ConfigClass.METADATA_SERVICE}collection/{collection_geid}/'
    response = requests.get(url, timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT)
    res = response.json()['result']
    if res:
        return res
    else:
        raise APIException(
            status_code=EAPIResponseCode.not_found.value, error_msg=f'Collection {collection_geid} does not exist'
        )
