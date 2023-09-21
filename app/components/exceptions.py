# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from abc import ABCMeta
from abc import abstractmethod
from http import HTTPStatus
from typing import Any
from typing import Dict


class ServiceException(Exception, metaclass=ABCMeta):
    """Base class for service exceptions."""

    domain: str = 'global'

    @property
    @abstractmethod
    def status(self) -> int:
        """HTTP status code applicable to the problem."""

        raise NotImplementedError

    @property
    @abstractmethod
    def code(self) -> str:
        """Component-specific error code."""

        raise NotImplementedError

    @property
    @abstractmethod
    def details(self) -> str:
        """Additional information with specific explanation for this occurrence of the problem."""

        raise NotImplementedError

    def dict(self) -> Dict[str, Any]:
        """Represent error as dictionary."""

        return {
            'code': f'{self.domain}.{self.code}',
            'details': self.details,
        }


class UnhandledException(ServiceException):
    """Raised when unhandled/unexpected internal error occurred."""

    @property
    def status(self) -> int:
        return HTTPStatus.INTERNAL_SERVER_ERROR

    @property
    def code(self) -> str:
        return 'unhandled_exception'

    @property
    def details(self) -> str:
        return 'Unexpected Internal Server Error'


class APIException(ServiceException):
    """Backwards compatible legacy all-purpose exception."""

    def __init__(self, status_code: int, error_msg: str) -> None:
        self.status_code = status_code
        self.error_msg = error_msg
        self.content = {
            'code': self.status_code,
            'error_msg': self.error_msg,
            'result': '',
        }

    @property
    def status(self) -> int:
        return self.status_code

    @property
    def code(self) -> str:
        return 'legacy_api_exception'

    @property
    def details(self) -> str:
        return self.error_msg
