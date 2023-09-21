# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import FastAPI

from api import api_archive
from api import api_auth
from api import api_bridge
from api import api_contact_us
from api import api_dataset_rest_proxy
from api import api_download
from api import api_email
from api import api_invitation
from api import api_lineage_provenance
from api import api_preview
from api import api_project
from api import api_project_files
from api import api_project_v2
from api import api_provenance
from api import api_task_stream
from api import api_upload
from api import api_users
from api import api_workbench
from api.api_announcement import announcement
from api.api_container import api_aduser_update
from api.api_container import api_container_user
from api.api_container import api_containers
from api.api_container import api_folder_creation
from api.api_container import user_operation
from api.api_copy_request import copy_request
from api.api_data_manifest import data_manifest
from api.api_dataset import api_activity_logs
from api.api_dataset import api_folder
from api.api_dataset import api_schema
from api.api_dataset import api_schema_template
from api.api_dataset import api_validate
from api.api_dataset import api_versions
from api.api_files import favourites
from api.api_files import file_ops
from api.api_files import meta
from api.api_files import vfolder_ops
from api.api_health import health
from api.api_kg import kg
from api.api_notification import notification
from api.api_permissions import permissions
from api.api_resource_request import resource_request
from api.api_tags import api_batch_tags_operation
from api.api_tags import api_tags_operation
from api.api_user_event import event
from api.api_workspace import workspace


def api_registry(app: FastAPI) -> None:
    app.include_router(api_activity_logs.router, prefix='/v1')
    app.include_router(announcement.router, prefix='/v1')
    app.include_router(api_archive.router, prefix='/v1')
    app.include_router(api_auth.router, prefix='/v1')
    app.include_router(api_contact_us.router, prefix='/v1')
    app.include_router(api_aduser_update.router, prefix='/v1')
    app.include_router(api_container_user.router, prefix='/v1')
    app.include_router(api_containers.router, prefix='/v1')
    app.include_router(api_folder_creation.router, prefix='/v1')
    app.include_router(user_operation.router, prefix='/v1')
    app.include_router(copy_request.router, prefix='/v1')
    app.include_router(data_manifest.router, prefix='/v1')
    app.include_router(api_dataset_rest_proxy.router, prefix='/v1')
    app.include_router(api_folder.router, prefix='/v1')
    app.include_router(api_invitation.router, prefix='/v1')
    app.include_router(api_schema.router, prefix='/v1')
    app.include_router(api_schema_template.router, prefix='/v1')
    app.include_router(api_validate.router, prefix='/v1')
    app.include_router(api_versions.router, prefix='/v1')
    app.include_router(api_download.router, prefix='/v2')
    app.include_router(api_task_stream.router, prefix='/v1')
    app.include_router(api_email.router, prefix='/v1')
    app.include_router(file_ops.router, prefix='/v1')
    app.include_router(meta.router, prefix='/v1')
    app.include_router(vfolder_ops.router, prefix='/v1')
    app.include_router(kg.router, prefix='/v1')
    app.include_router(notification.router, prefix='/v1')
    app.include_router(api_preview.router, prefix='/v1')
    app.include_router(api_project.router, prefix='/v1')
    app.include_router(api_project_v2.router, prefix='/v1')
    app.include_router(api_provenance.router, prefix='/v1')
    app.include_router(api_batch_tags_operation.router, prefix='/v2')
    app.include_router(api_tags_operation.router, prefix='/v2')
    app.include_router(event.router, prefix='/v1')
    app.include_router(api_users.router, prefix='/v1')
    app.include_router(api_workbench.router, prefix='/v1')
    app.include_router(resource_request.router, prefix='/v1')
    app.include_router(health.router, prefix='/v1')
    app.include_router(api_project_files.router, prefix='/v1')
    app.include_router(favourites.router, prefix='/v1')
    app.include_router(api_bridge.router, prefix='/v1')
    app.include_router(workspace.router, prefix='/v1')
    app.include_router(api_upload.router, prefix='/v1')
    app.include_router(permissions.router, prefix='/v1')
    app.include_router(api_lineage_provenance.router, prefix='/v1')
