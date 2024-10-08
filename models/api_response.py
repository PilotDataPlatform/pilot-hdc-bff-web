# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from enum import Enum

from fastapi.responses import JSONResponse


class EAPIResponseCode(Enum):
    success = 200
    internal_error = 500
    bad_request = 400
    not_found = 404
    forbidden = 403
    unauthorized = 401
    conflict = 409


class APIResponse:
    def __init__(self):
        self._attribute_map = {
            'code': EAPIResponseCode.success.value,
            'error_msg': '',
            'result': '',
            'page': 1,
            'total': 1,
            'num_of_pages': 1,
        }

    def json_response(self) -> JSONResponse:
        return JSONResponse(status_code=self.code, content=self._attribute_map)

    @property
    def to_dict(self):
        return self._attribute_map

    @property
    def code(self):
        return self._attribute_map['code']

    @property
    def error_msg(self):
        return self._attribute_map['code']

    @property
    def result(self):
        return self._attribute_map['result']

    @property
    def page(self):
        return self._attribute_map['page']

    @property
    def total(self):
        return self._attribute_map['total']

    @property
    def num_of_pages(self):
        return self._attribute_map['num_of_pages']

    def set_code(self, code):
        if isinstance(code, int):
            self._attribute_map['code'] = code
        else:
            self._attribute_map['code'] = code.value

    def set_error_msg(self, error_msg: str):
        self._attribute_map['error_msg'] = error_msg

    def set_result(self, result):
        self._attribute_map['result'] = result

    def set_response(self, key, value):
        self._attribute_map[key] = value

    def set_page(self, page_current: int):
        self._attribute_map['page'] = page_current

    def set_total(self, total_rows: int):
        self._attribute_map['total'] = total_rows

    def set_num_of_pages(self, num_of_pages: int):
        self._attribute_map['num_of_pages'] = num_of_pages
