# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import logging
from functools import lru_cache
from typing import Any

from common import VaultClient
from pydantic import BaseSettings
from pydantic import Extra


class VaultConfig(BaseSettings):
    """Store vault related configuration."""

    APP_NAME: str = 'bff-web'
    CONFIG_CENTER_ENABLED: bool = False

    VAULT_URL: str | None
    VAULT_CRT: str | None
    VAULT_TOKEN: str | None

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


def load_vault_settings(settings: BaseSettings) -> dict[str, Any]:
    config = VaultConfig()

    if not config.CONFIG_CENTER_ENABLED:
        return {}

    client = VaultClient(config.VAULT_URL, config.VAULT_CRT, config.VAULT_TOKEN)
    return client.get_from_vault(config.APP_NAME)


class Settings(BaseSettings):
    """Store service configuration settings."""

    APP_NAME: str = 'bff-web'
    HOST: str = '0.0.0.0'
    PORT: int = 5060
    WORKERS: int = 1
    RELOAD: bool = False
    LOGGING_LEVEL: int = logging.INFO
    LOGGING_FORMAT: str = 'json'

    SERVICE_CLIENT_TIMEOUT: int = 5

    PROJECT_NAME: str = 'Pilot'

    STARTING_PROJECT_CODE: str = 'indoctestproject'

    FORBIDDEN_CONTAINER_CODES: set[str] = {'platform'}

    CORE_ZONE_LABEL: str = 'Core'
    GREENROOM_ZONE_LABEL: str = 'Greenroom'

    KEYCLOAK_REALM: str

    # Services
    DATAOPS_SERVICE: str
    AUTH_SERVICE: str
    PROVENANCE_SERVICE: str
    NOTIFY_SERVICE: str
    DATASET_SERVICE: str
    DOWNLOAD_SERVICE_CORE: str
    DOWNLOAD_SERVICE_GR: str
    UPLOAD_SERVICE: str
    APPROVAL_SERVICE: str
    METADATA_SERVICE: str
    PROJECT_SERVICE: str
    KG_SERVICE: str
    SEARCH_SERVICE: str
    WORKSPACE_SERVICE: str

    REDIS_HOST: str = '127.0.0.1'
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ''

    USER_CACHE_EXPIRY: int = 180
    ENABLE_USER_CACHE: bool = True
    ENABLE_CACHE: bool = True

    # Email addresses
    EMAIL_SUPPORT: str
    EMAIL_SUPPORT_REPLY_TO: str
    EMAIL_ADMIN: str
    EMAIL_HELPDESK: str

    EMAIL_CONTACT_US_SUBJECT: str = 'ACTION REQUIRED - {project_name} Support Request Submitted'
    EMAIL_CONTACT_US_CONFIRMATION_SUBJECT: str = '{project_name}: Confirmation of Contact Email'
    EMAIL_PROJECT_REGISTER_URL: str = ''
    EMAIL_PROJECT_SUPPORT_URL: str = ''

    # Domain
    SITE_DOMAIN: str

    # Invitation
    INVITATION_URL_LOGIN: str

    # Resource request
    RESOURCE_REQUEST_ADMIN: str

    OPEN_TELEMETRY_ENABLED: bool = False
    OPEN_TELEMETRY_HOST: str = '127.0.0.1'
    OPEN_TELEMETRY_PORT: int = 6831

    ENABLE_PROMETHEUS_METRICS: bool = False

    PACT_BROKER_URL: str = ''

    def modify_values(self, settings):
        settings.METADATA_SERVICE = settings.METADATA_SERVICE + '/v1/'
        settings.APPROVAL_SERVICE = settings.APPROVAL_SERVICE + '/v1/'
        DATAOPS_HOST = settings.DATAOPS_SERVICE
        settings.DATAOPS_SERVICE = DATAOPS_HOST + '/v1/'
        settings.DATAOPS_SERVICE_v2 = DATAOPS_HOST + '/v2/'
        settings.AUTH_SERVICE = settings.AUTH_SERVICE + '/v1/'
        settings.PROVENANCE_SERVICE = settings.PROVENANCE_SERVICE + '/v1/'
        settings.DATASET_SERVICE = settings.DATASET_SERVICE + '/v1/'
        settings.DOWNLOAD_SERVICE_CORE_V2 = settings.DOWNLOAD_SERVICE_CORE + '/v2/'
        settings.DOWNLOAD_SERVICE_GR_V2 = settings.DOWNLOAD_SERVICE_GR + '/v2/'
        settings.WORKSPACE_SERVICE = settings.WORKSPACE_SERVICE + '/v1/'
        settings.REDIS_URL = f'redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}'
        settings.ZONE_LABEL_MAPPING = {
            0: settings.GREENROOM_ZONE_LABEL,
            1: settings.CORE_ZONE_LABEL,
        }
        settings.LABEL_ZONE_MAPPING = {value.lower(): key for key, value in settings.ZONE_LABEL_MAPPING.items()}

        for setting_var in ('EMAIL_CONTACT_US_SUBJECT', 'EMAIL_CONTACT_US_CONFIRMATION_SUBJECT'):
            subject = getattr(settings, setting_var).format(project_name=settings.PROJECT_NAME)
            setattr(settings, setting_var, subject)

        return settings

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = Extra.allow

        @classmethod
        def customise_sources(cls, init_settings, env_settings, file_secret_settings):
            return init_settings, env_settings, load_vault_settings, file_secret_settings


@lru_cache(1)
def get_settings() -> Settings:
    settings = Settings()
    settings = settings.modify_values(settings)
    return settings


ConfigClass = get_settings()
