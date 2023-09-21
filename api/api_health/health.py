# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import APIRouter
from fastapi.responses import Response
from fastapi_utils import cbv

router = APIRouter(tags=['Health'])


@cbv.cbv(router)
class Health:
    @router.get(
        '/health',
        summary='Health check',
    )
    async def get(self):
        return Response(status_code=204)
