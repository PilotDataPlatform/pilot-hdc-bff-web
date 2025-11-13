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

    async def test_list_dataset_version_sharing_requests_calls_dataset_service(
        self, httpx_mock, fake, dataset_service_client
    ):
        parameters = fake.pydict(allowed_types=[str, int])

        query_string = '&'.join(f'{key}={value}' for key, value in parameters.items())

        httpx_mock.add_response(
            method='GET', url=f'{dataset_service_client.endpoint_v1}/version-sharing-requests/?{query_string}'
        )

        response = await dataset_service_client.list_dataset_version_sharing_requests(parameters)

        assert response.status_code == 200

    async def test_get_dataset_version_sharing_request_calls_dataset_service(
        self, httpx_mock, fake, dataset_service_client
    ):
        version_sharing_request_id = fake.uuid4()

        httpx_mock.add_response(
            method='GET',
            url=f'{dataset_service_client.endpoint_v1}/version-sharing-requests/{version_sharing_request_id}',
        )

        response = await dataset_service_client.get_dataset_version_sharing_request(version_sharing_request_id)

        assert response.status_code == 200

    async def test_create_dataset_version_sharing_request_calls_dataset_service(
        self, httpx_mock, fake, dataset_service_client
    ):
        httpx_mock.add_response(method='POST', url=f'{dataset_service_client.endpoint_v1}/version-sharing-requests/')

        response = await dataset_service_client.create_dataset_version_sharing_request(
            fake.uuid4(), fake.project_code(), fake.user_name()
        )

        assert response.status_code == 200

    async def test_process_dataset_version_sharing_request_calls_dataset_service(
        self, httpx_mock, fake, dataset_service_client
    ):
        version_sharing_request_id = fake.uuid4()

        httpx_mock.add_response(
            method='PATCH',
            url=f'{dataset_service_client.endpoint_v1}/version-sharing-requests/{version_sharing_request_id}',
        )

        response = await dataset_service_client.process_dataset_version_sharing_request(
            version_sharing_request_id, fake.user_name(), 'declined'
        )

        assert response.status_code == 200

    async def test_start_version_sharing_request_calls_dataset_service(self, httpx_mock, fake, dataset_service_client):
        version_sharing_request_id = fake.uuid4()

        httpx_mock.add_response(
            method='POST',
            url=f'{dataset_service_client.endpoint_v1}/version-sharing-requests/{version_sharing_request_id}/start',
        )

        response = await dataset_service_client.start_version_sharing_request(
            version_sharing_request_id, fake.uuid4(), fake.uuid4(), 'Bearer token'
        )

        assert response.status_code == 200
