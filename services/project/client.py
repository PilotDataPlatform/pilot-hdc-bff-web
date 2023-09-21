# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from common import ProjectClient
from fastapi import Depends

from config import Settings
from config import get_settings


def get_project_service_client(settings: Settings = Depends(get_settings)) -> ProjectClient:
    """Get project service client as a FastAPI dependency."""

    return ProjectClient(settings.PROJECT_SERVICE, settings.REDIS_URL)
