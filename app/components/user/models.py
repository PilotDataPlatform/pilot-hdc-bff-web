# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Any
from uuid import UUID

from models.user_type import EUserRole
from services.project.client import ProjectServiceClient


class CurrentUser(dict[str, Any]):
    """Current user model."""

    def __init__(self, *args: Any) -> None:
        super().__init__(*args)

        self._user_projects = None

    @property
    def id(self) -> UUID:
        return UUID(self['user_id'])

    @property
    def email(self) -> str:
        return self['email']

    @property
    def role(self) -> str:
        return self['role']

    @property
    def username(self) -> str:
        return self['username']

    @property
    def realm_roles(self) -> list[str]:
        return self['realm_roles']

    @property
    def is_platform_admin(self) -> bool:
        return 'platform-admin' in self.realm_roles

    def get_project_roles(self) -> dict[str, str]:
        """Return the projects in which the user participates together with the role in that project."""

        if self._user_projects is None:
            self._user_projects = {}

            project_related_roles = EUserRole.get_project_related()

            for realm_role in self.realm_roles:
                try:
                    project_code, project_role = realm_role.split('-', 1)
                    assert project_code != 'platform'  # Edge case for "platform-admin" role
                except (ValueError, AssertionError):
                    continue

                if project_role in project_related_roles:
                    self._user_projects[project_code] = project_role

        return self._user_projects

    def get_projects_with_role(self, matching_role: str) -> list[str]:
        """Return a list of projects in which the user has a matching role."""

        return [code for code, role in self.get_project_roles().items() if role == matching_role]

    async def can_access_dataset(self, dataset: dict[str, Any], project_service_client: ProjectServiceClient) -> bool:
        """Return true if the user has permission to access the dataset."""

        if dataset['creator'] == self.username:
            return True

        dataset_project_id = dataset.get('project_id', None)
        if dataset_project_id is None:
            return False

        user_project_codes = self.get_projects_with_role('admin')
        user_project_ids = await project_service_client.convert_project_codes_into_ids(user_project_codes)

        return UUID(dataset_project_id) in user_project_ids

    def can_access_project(self, project_code: str) -> bool:
        """Return true if the user has permission to access the project."""

        if self.is_platform_admin:
            return True

        return project_code in self.get_project_roles().keys()
