# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import List

from pydantic import BaseModel

from .api_response import APIResponse


class POSTProjectFileResponse(APIResponse):
    result: dict


class POSTProjectFile(BaseModel):
    operator: str
    job_type: str
    current_folder_node: str
    parent_folder_id: str
    data: list
    folder_tags: list[str] = []


class ResumableResponse(BaseModel):
    result: dict


class ResumableUploadPOST(BaseModel):
    """Pre upload payload model."""

    class ObjectInfo(BaseModel):
        object_path: str
        item_id: str
        resumable_id: str

    object_infos: List[ObjectInfo]
