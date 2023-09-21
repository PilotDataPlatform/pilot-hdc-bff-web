# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import requests
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_utils import cbv

from app.auth import jwt_required
from app.logger import logger
from config import ConfigClass
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode
from services.dataset import get_dataset_by_code
from services.permissions_service.decorators import DatasetPermission

router = APIRouter(tags=['Dataset Validate'])


@cbv.cbv(router)
class BIDSValidator:
    current_identity: dict = Depends(jwt_required)

    @router.post(
        '/dataset/bids-validate',
        summary='verify a bids dataset.',
        dependencies=[Depends(DatasetPermission())],
    )
    async def post(self, request: Request):
        _res = APIResponse()
        payload = await request.json()
        dataset_code = payload.get('dataset_code', None)
        if not dataset_code:
            _res.set_code(EAPIResponseCode.bad_request)
            _res.set_error_msg('dataset_code is missing in payload')
            return _res.json_response()

        logger.info(f'Call API for validating dataset: {dataset_code}')

        try:
            dataset_node = await get_dataset_by_code(dataset_code)
            if dataset_node['type'] != 'BIDS':
                _res.set_code(EAPIResponseCode.bad_request)
                _res.set_result('Dataset is not BIDS type')
                return _res.json_response()
        except Exception as e:
            _res.code = EAPIResponseCode.bad_request
            _res.error_msg = f'error when get dataset node in dataset service: {e}'
            return _res.json_response()
        try:
            url = ConfigClass.DATASET_SERVICE + 'dataset/verify/pre'
            data = {'dataset_code': dataset_code, 'type': 'bids'}
            response = requests.post(
                url, headers=request.headers, json=data, timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT
            )
            return JSONResponse(content=response.json(), status_code=response.status_code)

        except Exception as e:
            _res.code = EAPIResponseCode.bad_request
            _res.error_msg = f'error when verify dataset in service dataset: {e}'
            return _res.json_response()


@cbv.cbv(router)
class BIDSResult:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/dataset/bids-validate/{dataset_code}',
        summary='get bids validate result',
        dependencies=[Depends(DatasetPermission())],
    )
    def get(self, dataset_code: str):
        try:
            url = ConfigClass.DATASET_SERVICE + f'dataset/bids-msg/{dataset_code}'
            response = requests.get(url, timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT)
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except Exception as e:
            _res = APIResponse()
            _res.code = EAPIResponseCode.bad_request
            _res.error_msg = f'error when get dataset bids result in service dataset: {e}'
            return _res.json_response()
