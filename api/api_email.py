# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import re

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi_utils import cbv
from httpx import AsyncClient

from app.auth import jwt_required
from app.components.user.models import CurrentUser
from app.logger import logger
from config import ConfigClass
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode
from services.notifier_services.email_service import SrvEmail
from services.permissions_service.decorators import PermissionsCheck

router = APIRouter(tags=['Email'])


@cbv.cbv(router)
class EmailRestful:
    current_identity: CurrentUser = Depends(jwt_required)

    @router.post(
        '/email',
        summary='Send notification email to platform users',
        dependencies=[Depends(PermissionsCheck('notification', '*', 'manage'))],
    )
    async def post(self, request: Request):
        """Send notification email to platform users."""

        response = APIResponse()

        data = await request.json()
        logger.info(f'Start Notification Email: {data}')
        send_to_all_active = data.get('send_to_all_active')
        emails = data.get('emails')
        subject = data.get('subject')
        message_body = data.get('message_body')

        pattern = re.compile(r'([^\s])')
        msg_match = re.search(pattern, message_body)
        subject_match = re.search(pattern, subject)

        if not msg_match or not subject_match:
            error = 'Content other then whitespace is required'
            response.set_code(EAPIResponseCode.bad_request)
            response.set_result(error)
            logger.error(error)
            return response.json_response()

        if not subject or not message_body or not (emails or send_to_all_active):
            error = 'Missing fields'
            response.set_code(EAPIResponseCode.bad_request)
            response.set_result(error)
            logger.error(error)
            return response.json_response()

        if emails and send_to_all_active:
            error = "Can't set both emails and send_to_all_active"
            response.set_code(EAPIResponseCode.bad_request)
            response.set_result(error)
            logger.error(error)
            return response.json_response()

        if send_to_all_active:
            payload = {'status': 'active', 'page_size': 1000}
            async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
                res = await client.get(ConfigClass.AUTH_SERVICE + 'users', params=payload)
            users = res.json()['result']
            emails = [i['email'] for i in users if i.get('email')]
        else:
            if not isinstance(emails, list):
                error = 'emails must be list'
                response.set_result(EAPIResponseCode.bad_request)
                response.set_result(error)
                logger.error(error)
                return response.json_response()

        email_service = SrvEmail()
        email_service.send(subject, emails, content=message_body)

        logger.info('Notification Email Sent')
        response.set_code(EAPIResponseCode.success)
        response.set_result('success')
        return response.json_response()
