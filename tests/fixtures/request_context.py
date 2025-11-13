# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import pytest
from fastapi.datastructures import Headers
from fastapi.requests import Request

from app.components.request.context import RequestContext
from app.components.request.context import get_request_context


@pytest.fixture
def request_context(settings) -> RequestContext:
    request = Request(scope={'type': 'http', 'headers': Headers().raw})
    return get_request_context(request, settings)
