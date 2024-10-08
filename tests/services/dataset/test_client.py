# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.


class TestDatasetServiceClient:
    async def test_get_dataset_by_id_calls_dataset_service(self, httpx_mock, fake, dataset_service_client):
        dataset_id = fake.dataset_id()
        httpx_mock.add_response(
            method='GET',
            url=f'{dataset_service_client.endpoint_v1}/datasets/{dataset_id}',
            json={'id': dataset_id},
        )

        dataset = await dataset_service_client.get_dataset_by_id(dataset_id)

        assert dataset['id'] == dataset_id

    async def test_get_dataset_by_code_calls_dataset_service(self, httpx_mock, fake, dataset_service_client):
        dataset_code = fake.dataset_code()
        httpx_mock.add_response(
            method='GET',
            url=f'{dataset_service_client.endpoint_v1}/datasets/{dataset_code}',
            json={'code': dataset_code},
        )

        dataset = await dataset_service_client.get_dataset_by_code(dataset_code)

        assert dataset['code'] == dataset_code

    async def test_list_datasets_calls_dataset_service(self, httpx_mock, fake, dataset_service_client):
        parameters = fake.pydict(allowed_types=[str, int])

        query_string = '&'.join(f'{key}={value}' for key, value in parameters.items())

        httpx_mock.add_response(method='GET', url=f'{dataset_service_client.endpoint_v1}/datasets/?{query_string}')

        response = await dataset_service_client.list_datasets(parameters)

        assert response.status_code == 200
