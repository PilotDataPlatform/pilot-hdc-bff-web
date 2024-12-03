# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import json
from typing import Any

from pydantic import BaseModel


class BaseSchema(BaseModel):
    """Base class for all available schemas."""

    def to_payload(self, **kwds: Any) -> dict[str, Any]:
        return json.loads(self.json(**kwds))
