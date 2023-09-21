# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from enum import Enum

from pydantic import BaseModel


class Entities(str, Enum):
    dataset = 'dataset'
    project = 'project'


class AddVisits(BaseModel):
    code: str
    entity: Entities


class AddVisitsResponse(BaseModel):
    result: str
    code: int


class GetRecentVisits(BaseModel):
    entity: Entities
    last: int

    class Config:
        use_enum_values = True
