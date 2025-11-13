# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import pytest

from services.bridge import BridgeService
from services.bridge import get_bridge_service


@pytest.fixture
async def bridge_service(project_service_client, dataset_service_client) -> BridgeService:
    return await get_bridge_service(project_service_client, dataset_service_client)
