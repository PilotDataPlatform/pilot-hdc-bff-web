# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from api.module_api import module_api

datasets_entity_ns = module_api.namespace(
    'Portal Containers Actions', description='Operation on containers', path='/v1/containers'
)
users_entity_ns = module_api.namespace('Portal User Actions', description='Operation on users', path='/v1/users')
