# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import datetime as dt
import json
from logging import LogRecord
from logging import getLevelName

from app.components.logging import JsonFormatter
from app.components.logging import configure_logging


class TestJsonFormatter:
    def test_format_converts_log_record_into_expected_json_string(self, fake):
        logger = fake.word()
        level = fake.pyint(0, 5) * 10
        message = fake.word()
        exception_message = fake.text()
        exception = Exception(exception_message)
        exc_info = (type(exception), exception, exception.__traceback__)
        record = LogRecord(logger, level, '', 0, message, None, exc_info)
        asctime = dt.datetime.fromtimestamp(record.created, tz=dt.timezone.utc).isoformat()
        expected_string = json.dumps(
            {
                'asctime': asctime,
                'level': getLevelName(level),
                'logger': logger,
                'message': message,
                'exc_info': f'Exception: {exception_message}',
            }
        )

        received_string = JsonFormatter().format(record)

        assert received_string == expected_string


class TestLogging:
    def test_configure_logging_calls_dict_configurator_with_expected_config(self, mocker, fake):
        mock = mocker.patch('logging.config.dictConfig')
        level = fake.pyint(0, 5) * 10
        expected_config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'default': {'format': '%(asctime)s\t%(levelname)s\t' '[%(name)s]\t%(message)s'},
                'json': {'()': JsonFormatter},
            },
            'handlers': {
                'stdout': {
                    'formatter': 'default',
                    'class': 'logging.StreamHandler',
                    'stream': 'ext://sys.stdout',
                }
            },
            'loggers': {
                'pilot': {'handlers': ['stdout'], 'level': level},
                'asyncio': {'handlers': ['stdout'], 'level': level},
                'uvicorn': {'handlers': ['stdout'], 'level': level},
            },
        }

        configure_logging(level, 'non-existing')

        mock.assert_called_once_with(expected_config)
