# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import atexit

import pytest
from pact import Consumer
from pact import Provider

from config import ConfigClass


@pytest.fixture(scope='session')
def pact_auth_service_init():
    """Create client with mock auth service response."""
    pact = Consumer('BffWebService', version='2.0.12').has_pact_with(
        Provider('AuthService'),
        pact_dir='tests_contract/consumer/pacts',
        broker_base_url=ConfigClass.PACT_BROKER_URL,
        publish_to_broker=True,
    )
    pact.start_service()
    atexit.register(pact.stop_service)
    yield pact
    pact.stop_service()
