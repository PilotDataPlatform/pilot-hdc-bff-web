# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import requests

from config import ConfigClass
from models.models_item import ItemStatus
from services.permissions_service.utils import get_project_role


def has_permissions(template_id, file_node, current_identity):  # noqa: C901
    try:
        response = requests.get(
            ConfigClass.METADATA_SERVICE + f'template/{template_id}/', timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT
        )
        manifest = response.json()['result']
        if not manifest:
            return False
    except Exception as e:
        error_msg = {'result': str(e)}
        return error_msg, 500

    if current_identity['role'] != 'admin':
        role = get_project_role(manifest['project_code'], current_identity)
        if role == 'contributor':
            if file_node.get('status') == ItemStatus.ACTIVE:
                root_folder = file_node['parent_path'].split('/')[0]
                if root_folder != current_identity['username']:
                    return False
            else:
                root_folder = file_node['restore_path'].split('/')[0]
                if root_folder != current_identity['username']:
                    return False
        elif role == 'collaborator':
            if file_node['zone'] == 0:
                if file_node.get('status') == ItemStatus.ACTIVE:
                    root_folder = file_node['parent_path'].split('/')[0]
                    if root_folder != current_identity['username']:
                        return False
                else:
                    root_folder = file_node['restore_path'].split('/')[0]
                    if root_folder != current_identity['username']:
                        return False
    return True
