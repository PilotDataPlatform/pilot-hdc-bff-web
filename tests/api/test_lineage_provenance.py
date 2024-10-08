# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from config import ConfigClass


async def test_lineage_provenance_200(test_async_client, httpx_mock):
    item_id = '93bfc2ba-fa6c-46cc-a257-fa4d41c109df'
    metadata_url = f'{ConfigClass.METADATA_SERVICE}lineage/{item_id}/'
    metadata_response = {'result': {'lineage': {}, 'provenance': {}}}
    httpx_mock.add_response(method='GET', url=metadata_url, json=metadata_response)
    response = await test_async_client.get(f'/v1/lineage/{item_id}/')
    assert response.status_code == 200
    assert len(response.json()['result']) == 2
