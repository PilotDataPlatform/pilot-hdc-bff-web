# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from uuid import UUID

import pytest
from pydantic import BaseModel
from pytest_httpx import HTTPXMock

from services.project.client import ProjectServiceClient
from services.project.client import get_project_service_client
from tests.fixtures.fake import Faker


class Project(BaseModel):
    id: UUID
    code: str


class ProjectFactory:
    def __init__(self, fake: Faker, httpx_mock: HTTPXMock, endpoint: str) -> None:
        self.fake = fake
        self.httpx_mock = httpx_mock
        self.endpoint_v1 = f'{endpoint}/v1'

    def generate(self, *, id_: UUID = ..., code: str = ...) -> Project:
        if id_ is ...:
            id_ = UUID(self.fake.project_id())

        if code is ...:
            code = self.fake.project_code()

        return Project(id=id_, code=code)

    def _mock_retrieval(self, url: str, project: Project) -> Project:
        self.httpx_mock.add_response(method='GET', url=url, text=project.json())
        return project

    def mock_retrieval_by_code(self, project: Project = ...) -> Project:
        if project is ...:
            project = self.generate()

        return self._mock_retrieval(f'{self.endpoint_v1}/projects/{project.code}', project)

    def mock_retrieval_by_id(self, project: Project = ...) -> Project:
        if project is ...:
            project = self.generate()

        return self._mock_retrieval(f'{self.endpoint_v1}/projects/{project.id}', project)


@pytest.fixture
def project_factory(fake, httpx_mock, settings) -> ProjectFactory:
    return ProjectFactory(fake, httpx_mock, settings.PROJECT_SERVICE)


@pytest.fixture
def project_service_client(settings) -> ProjectServiceClient:
    return get_project_service_client(settings)
