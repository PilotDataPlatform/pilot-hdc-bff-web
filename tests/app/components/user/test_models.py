# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import random
from uuid import UUID

import pytest

from app.components.user.models import CurrentUser
from models.user_type import EUserRole


class TestCurrentUser:
    def test_id_returns_user_id_value_as_uuid(self, fake):
        user_id = fake.uuid4()
        user = CurrentUser({'user_id': user_id})

        assert user.id == UUID(user_id)

    def test_email_returns_email_value(self, fake):
        email = fake.email()
        user = CurrentUser({'email': email})

        assert user.email == email

    def test_role_returns_role_value(self, fake):
        role = fake.pystr()
        user = CurrentUser({'role': role})

        assert user.role == role

    def test_username_returns_username_value(self, fake):
        username = fake.pystr()
        user = CurrentUser({'username': username})

        assert user.username == username

    def test_realm_roles_returns_realm_roles_value(self, fake):
        realm_roles = [fake.pystr()]
        user = CurrentUser({'realm_roles': realm_roles})

        assert user.realm_roles == realm_roles

    def test_get_project_roles_returns_dict_with_projects_and_roles_based_on_realm_roles(self, fake):
        project_code = fake.project_code()
        project_role = random.choice(EUserRole.get_project_related())
        realm_roles = [f'{project_code}-{project_role}']
        expected_project_roles = {project_code: project_role}

        received_project_roles = CurrentUser({'realm_roles': realm_roles}).get_project_roles()

        assert received_project_roles == expected_project_roles

    def test_get_projects_with_role_returns_list_with_project_codes_where_role_matches(self, fake):
        project_codes = [fake.project_code(), fake.project_code()]
        project_roles = random.sample(EUserRole.get_project_related(), len(project_codes))
        realm_roles = [f'{code}-{role}' for code, role in zip(project_codes, project_roles)]
        role = random.choice(project_roles)
        expected_projects = [project_codes[project_roles.index(role)]]

        received_projects = CurrentUser({'realm_roles': realm_roles}).get_projects_with_role(role)

        assert received_projects == expected_projects

    async def test_can_access_dataset_returns_true_when_username_matches_dataset_creator(
        self, fake, project_service_client
    ):
        username = fake.pystr()
        user = CurrentUser({'username': username})

        dataset = {'creator': username}

        assert await user.can_access_dataset(dataset, project_service_client) is True

    async def test_can_access_dataset_returns_false_when_username_does_not_match_dataset_creator(
        self, fake, project_service_client
    ):
        user = CurrentUser({'username': fake.pystr()})

        dataset = {'creator': fake.pystr()}

        assert await user.can_access_dataset(dataset, project_service_client) is False

    @pytest.mark.parametrize(
        'project_factory_method,user_role,expected_result',
        [
            ('mock_retrieval_by_code', EUserRole.admin, True),
            ('generate', EUserRole.contributor, False),
        ],
    )
    async def test_can_access_dataset_returns_expected_result_depending_on_user_role(
        self, project_factory_method, user_role, expected_result, fake, mocker, project_factory, project_service_client
    ):
        """When current user is not dataset creator and has different (admin or contributor) roles in the project linked
        with the dataset."""

        project = getattr(project_factory, project_factory_method)()

        realm_roles = [f'{project.code}-{user_role.name}']
        user = CurrentUser({'username': fake.pystr(), 'realm_roles': realm_roles})

        dataset = {'creator': fake.pystr(), 'project_id': str(project.id)}

        convert_codes_method = mocker.spy(project_service_client, 'convert_project_codes_into_ids')

        assert await user.can_access_dataset(dataset, project_service_client) is expected_result

        convert_codes_method.assert_called_once()
