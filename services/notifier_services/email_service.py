# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import json
from typing import List

import httpx
import requests

from config import ConfigClass
from models.service_meta_class import MetaService


class SrvEmail(metaclass=MetaService):
    def send(
        self,
        subject,
        receiver: List[str],
        content=None,
        msg_type='plain',
        attachments=None,
        sender=ConfigClass.EMAIL_SUPPORT_REPLY_TO,
        template=None,
        template_kwargs=None,
    ):
        if attachments is None:
            attachments = []
        if template_kwargs is None:
            template_kwargs = {}

        url = ConfigClass.NOTIFY_SERVICE + '/v1/email/'
        payload = {
            'subject': subject,
            'sender': sender,
            'receiver': receiver,
            'msg_type': msg_type,
            'attachments': attachments,
        }
        if content:
            payload['message'] = content
        if template:
            payload['template'] = template
            payload['template_kwargs'] = template_kwargs
        res = requests.post(url=url, json=payload, timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT)
        return json.loads(res.text)

    async def async_send(
        self,
        subject,
        receiver: List[str],
        content=None,
        msg_type='plain',
        attachments=None,
        sender=ConfigClass.EMAIL_SUPPORT_REPLY_TO,
        template=None,
        template_kwargs=None,
    ):
        if attachments is None:
            attachments = []
        if template_kwargs is None:
            template_kwargs = {}

        url = ConfigClass.NOTIFY_SERVICE + '/v1/email/'
        payload = {
            'subject': subject,
            'sender': sender,
            'receiver': receiver,
            'msg_type': msg_type,
            'attachments': attachments,
        }
        if content:
            payload['message'] = content
        if template:
            payload['template'] = template
            payload['template_kwargs'] = template_kwargs
        async with httpx.AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
            response = await client.post(url, json=payload)
        return response.json()
