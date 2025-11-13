# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_utils import cbv
from starlette.datastructures import MultiDict

from app.auth import jwt_required
from app.components.exceptions import APIException
from app.components.user.models import CurrentUser
from app.logger import logger
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode
from services.dataset.client import DatasetServiceClient
from services.dataset.client import get_dataset_service_client
from services.project.client import ProjectServiceClient
from services.project.client import get_project_service_client
from services.search.client import SearchServiceClient
from services.search.client import get_search_service_client

router = APIRouter(tags=['Activity Logs'])


@cbv.cbv(router)
class ActivityLogs:
    current_identity: CurrentUser = Depends(jwt_required)
    dataset_service_client: DatasetServiceClient = Depends(get_dataset_service_client)
    project_service_client: ProjectServiceClient = Depends(get_project_service_client)
    search_service_client: SearchServiceClient = Depends(get_search_service_client)

    @router.get(
        '/activity-logs/{dataset_code}',
        summary='Fetch activity logs of a dataset from the search service',
    )
    async def get(self, dataset_code: str, request: Request) -> JSONResponse:
        """Fetch activity logs of a dataset."""

        _res = APIResponse()
        logger.info(f'Call API for fetching logs for dataset: {dataset_code}')

        try:
            dataset = await self.dataset_service_client.get_dataset_by_code(dataset_code=dataset_code)

            if not await self.current_identity.can_access_dataset(dataset, self.project_service_client):
                _res.set_code(EAPIResponseCode.forbidden)
                _res.set_result('No permission for this dataset')
                return _res.json_response()

            params = MultiDict(request.query_params)
            params['container_code'] = dataset['code']
            result = await self.search_service_client.get_dataset_activity_logs(params)
            logger.info('Successfully fetched data from search service')
            return result
        except APIException as e:
            _res.set_code(e.status_code)
            _res.set_result(e.error_msg)
            return _res.json_response()
        except Exception as e:
            logger.error(f'Failed to query dataset activity log from search service: {e}')
            _res.set_code(EAPIResponseCode.internal_error)
            _res.set_result(f'Failed to query dataset activity log from search service: {e}')
            return _res.json_response()
