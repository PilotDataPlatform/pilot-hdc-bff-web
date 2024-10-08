# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from enum import Enum


class EUserRole(Enum):
    site_admin = -1
    admin = 0
    collaborator = 1
    member = 2
    contributor = 3
    visitor = 4

    @classmethod
    def get_project_related(cls) -> list[str]:
        """Return list of roles user may have withing a project."""

        return [cls.admin.name, cls.collaborator.name, cls.contributor.name]


def map_role_front_to_sys(role: str):
    """return EUserRole Type."""
    return {
        'site-admin': EUserRole.site_admin,
        'admin': EUserRole.admin,
        'member': EUserRole.member,
        'contributor': EUserRole.contributor,
        'uploader': EUserRole.contributor,
        'visitor': EUserRole.visitor,
        'collaborator': EUserRole.collaborator,
    }.get(role, None)


def map_role_sys_to_front(role: EUserRole):
    """return string."""
    return {
        EUserRole.site_admin: 'site-admin',
        EUserRole.admin: 'admin',
        EUserRole.member: 'member',
        EUserRole.contributor: 'contributor',
        EUserRole.visitor: 'visitor',
        EUserRole.collaborator: 'collaborator',
    }.get(role, None)


def map_role_to_frontend(role: str):
    return {
        'site-admin': 'Platform Administrator',
        'admin': 'Project Administrator',
        'member': 'Member',
        'contributor': 'Project Contributor',
        'uploader': 'Project Contributor',
        'visitor': 'Visitor',
        'collaborator': 'Project Collaborator',
    }.get(role, 'Member')
