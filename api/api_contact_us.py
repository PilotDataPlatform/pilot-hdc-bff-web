# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import APIRouter
from fastapi import Request
from fastapi_utils import cbv

from app.logger import logger
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode
from models.contact_us import ContactUsForm
from services.contact_us_services.contact_us_manager import SrvContactUsManager

router = APIRouter(tags=['Contact Us'])


@cbv.cbv(router)
class ContactUsRestful:
    @router.post(
        '/contact',
        summary='Sends a contact us message',
    )
    async def post(self, request: Request):
        my_res = APIResponse()
        post_json = await request.json()
        logger.info(f'Start Creating Contact Us Email: {post_json}')
        contact_form = ContactUsForm(post_json)
        contact_mgr = SrvContactUsManager()
        await contact_mgr.send_contact_us_email(contact_form)
        my_res.set_result('[SUCCEED] Contact us Email Sent')
        logger.info('Contact Us Email Sent')
        my_res.set_code(EAPIResponseCode.success)
        return my_res.json_response()
