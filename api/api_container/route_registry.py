# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from models.api_meta_class import MetaAPI

from .api_aduser_update import ADUserUpdate
from .api_container_user import ContainerUser
from .api_containers import Container
from .api_containers import Containers
from .api_folder_creation import FolderCreation
from .namespace import datasets_entity_ns
from .namespace import users_entity_ns
from .user_operation import ContainerAdmins
from .user_operation import ContainerUsers
from .user_operation import UserContainerQuery
from .user_operation import Users


class APIContainer(metaclass=MetaAPI):
    def api_registry(self):
        datasets_entity_ns.add_resource(Containers, '/')

        datasets_entity_ns.add_resource(Container, '/<project_id>')

        datasets_entity_ns.add_resource(ContainerUsers, '/<project_id>/users')
        datasets_entity_ns.add_resource(ContainerAdmins, '/<project_id>/admins')

        datasets_entity_ns.add_resource(FolderCreation, '/<project_id>/folder')

        datasets_entity_ns.add_resource(ContainerUser, '/<project_id>/users/<username>')
        users_entity_ns.add_resource(Users, '/platform')
        users_entity_ns.add_resource(UserContainerQuery, '/<username>/containers')
        users_entity_ns.add_resource(ADUserUpdate, '')
