# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from uuid import UUID

from common import ProjectClient
from fastapi import Depends

from config import Settings
from config import get_settings


class ProjectServiceClient(ProjectClient):
    async def convert_project_codes_into_ids(self, project_codes: list[str]) -> list[UUID]:
        """Convert list of project codes into list of project ids."""

        project_ids = []
        for code in project_codes:
            project = await self.get(code=code)
            project_ids.append(UUID(project.id))

        return project_ids


def get_project_service_client(settings: Settings = Depends(get_settings)) -> ProjectServiceClient:
    """Get project service client as a FastAPI dependency."""

    return ProjectServiceClient(settings.PROJECT_SERVICE, settings.REDIS_URL, settings.ENABLE_CACHE)
