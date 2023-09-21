# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import pytest
from fastapi import HTTPException

from services.permissions_service.decorators import find_project_code


async def test_find_project_code_returns_none_when_called_without_arguments():
    result = await find_project_code()

    assert result is None


async def test_find_project_code_raises_exception_when_called_with_both_project_code_and_project_id():
    with pytest.raises(HTTPException) as e:
        await find_project_code(project_code='code', project_id='id')

    assert 'mutually exclusive' in e.value.detail


async def test_find_project_code_returns_project_code_when_project_code_is_set(fake):
    project_code = fake.project_code()
    received_project_code = await find_project_code(project_code=project_code)

    assert received_project_code == project_code


async def test_find_project_code_returns_project_code_when_project_id_is_set(fake, project_client):
    project_id = fake.project_id()
    project_code = fake.project_code()
    await project_client.create_project(project_id, project_code)

    received_project_code = await find_project_code(project_id=project_id, project_service_client=project_client)

    assert received_project_code == project_code
