# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import datetime
from datetime import timezone

import requests

from config import ConfigClass


def remove_user_from_project_group(project_code, user_email, logger):
    payload = {
        'operation_type': 'remove',
        'user_email': user_email,
        'group_code': project_code,
    }
    res = requests.put(
        url=ConfigClass.AUTH_SERVICE + 'user/group',
        json=payload,
        timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT,
    )
    if res.status_code != 200:
        logger.error(f'Error removing user from group in ad: {res.text} {res.status_code}')


def add_user_to_ad_group(user_email, project_code, logger):
    payload = {
        'operation_type': 'add',
        'user_email': user_email,
        'group_code': project_code,
    }
    res = requests.put(
        url=ConfigClass.AUTH_SERVICE + 'user/group',
        json=payload,
        timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT,
    )
    if res.status_code != 200:
        logger.error(f'Error adding user to group in ad: {res.text} {res.status_code}')

    return res.json().get('entry')


def helper_now_utc():
    dt = datetime.datetime.now()
    utc_time = dt.replace(tzinfo=timezone.utc)
    return utc_time
