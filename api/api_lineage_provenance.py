# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from fastapi_utils import cbv

from services.meta import get_lineage_provenance

router = APIRouter(tags=['Lineage & provenance'])


@cbv.cbv(router)
class LineageProvenance:
    @router.get(
        '/lineage/{item_id}/',
        summary='Get lineage and provenance for an item',
    )
    async def get_lineage_provenance(self, item_id: str) -> JSONResponse:
        """Get lineage and provenance for an item."""
        response = await get_lineage_provenance(item_id)
        return JSONResponse(content=response.json(), status_code=response.status_code)
