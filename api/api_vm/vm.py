# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Any
from typing import Dict

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.responses import Response

from app.auth import jwt_required
from app.components.user.models import CurrentUser
from app.logger import logger
from config import ConfigClass
from models.api_response import EAPIResponseCode
from services.auth.client import AuthServiceClient
from services.auth.client import get_auth_service_client
from services.notifier_services.email_service import SrvEmail

router = APIRouter(tags=['VM account management'])


@router.get(
    '/vm/user',
    summary='Find user by username',
)
async def find_user(
    request: Request, username: str, auth_client: AuthServiceClient = Depends(get_auth_service_client)
) -> JSONResponse:

    response = await auth_client.find_vm_user(username=username)
    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.post(
    '/vm/user/reset',
    summary='Reset VM user password',
)
async def reset_password(
    request: Request,
    body: Dict[str, Any],
    current_identity: CurrentUser = Depends(jwt_required),
    auth_client: AuthServiceClient = Depends(get_auth_service_client),
) -> Response:

    if current_identity['username'] != body['username']:
        error_msg = "Username doesn't match current user"
        return Response(content=error_msg, status_code=EAPIResponseCode.forbidden.value)

    try:
        user_email = current_identity['email']

        template_kwargs = {
            'admin_email': ConfigClass.EMAIL_SUPPORT,
            'hdc_url': ConfigClass.SITE_DOMAIN,
            'current_user': body['username'],
        }
        subject = f'VM password reset for {body["username"]}'
        email_sender = SrvEmail()
        logger.info(f'Sent email with {template_kwargs}')
        await email_sender.async_send(
            subject,
            [user_email],
            msg_type='html',
            template='resource_request/vm_password_reset.html',
            template_kwargs=template_kwargs,
        )
    except Exception as e:
        error_msg = f'Error sending email: {e}'
        return Response(content=error_msg, status_code=EAPIResponseCode.internal_error.value)

    response = await auth_client.reset_password(data=body)
    return JSONResponse(content=response.json(), status_code=response.status_code)
