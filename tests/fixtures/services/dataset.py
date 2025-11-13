# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from uuid import UUID

import pytest
from pydantic import BaseModel
from pytest_httpx import HTTPXMock

from services.dataset.client import DatasetServiceClient
from services.dataset.client import get_dataset_service_client
from tests.fixtures.fake import Faker


class Dataset(BaseModel):
    id: UUID
    code: str
    creator: str
    project_id: UUID


class DatasetFactory:
    def __init__(self, fake: Faker, httpx_mock: HTTPXMock, endpoint: str) -> None:
        self.fake = fake
        self.httpx_mock = httpx_mock
        self.endpoint_v1 = f'{endpoint}/v1'

    def generate(self, *, id_: UUID = ..., code: str = ..., creator: str = ..., project_id: UUID = ...) -> Dataset:
        if id_ is ...:
            id_ = UUID(self.fake.dataset_id())

        if code is ...:
            code = self.fake.dataset_code()

        if creator is ...:
            creator = self.fake.unique.user_name()

        if project_id is ...:
            project_id = UUID(self.fake.project_id())

        return Dataset(id=id_, code=code, creator=creator, project_id=project_id)

    def _mock_retrieval(self, url: str, dataset: Dataset) -> Dataset:
        self.httpx_mock.add_response(method='GET', url=url, text=dataset.json())
        return dataset

    def mock_retrieval_by_code(self, dataset: Dataset = ...) -> Dataset:
        if dataset is ...:
            dataset = self.generate()

        return self._mock_retrieval(f'{self.endpoint_v1}/datasets/{dataset.code}', dataset)

    def mock_retrieval_by_id(self, dataset: Dataset = ...) -> Dataset:
        if dataset is ...:
            dataset = self.generate()

        return self._mock_retrieval(f'{self.endpoint_v1}/datasets/{dataset.id}', dataset)


@pytest.fixture
def dataset_factory(fake, httpx_mock, settings) -> DatasetFactory:
    return DatasetFactory(fake, httpx_mock, settings.DATASET_SERVICE.replace('/v1/', ''))


@pytest.fixture
def dataset_service_client(request_context, settings) -> DatasetServiceClient:
    return get_dataset_service_client(request_context, settings)
