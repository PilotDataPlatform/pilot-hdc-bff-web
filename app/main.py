# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from common import ProjectException
from common import configure_logging
from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_fastapi_instrumentator import PrometheusFastApiInstrumentator

from app.api_registry import api_registry
from app.components.exceptions import APIException
from app.components.exceptions import ServiceException
from app.components.exceptions import UnhandledException
from app.logger import logger
from config import Settings
from config import get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Initialize and configure the application."""

    if settings is None:
        settings = get_settings()

    app = FastAPI(
        title='BFF Web',
        description='Backend for Frontend Web',
        docs_url='/v1/api-doc',
        redoc_url='/v1/api-redoc',
    )

    setup_logging(settings)
    setup_routers(app)
    setup_middlewares(app, settings)
    setup_exception_handlers(app)
    setup_metrics(app, settings)
    setup_tracing(app, settings)

    return app


def setup_logging(settings: Settings) -> None:
    """Configure the application logging."""

    configure_logging(settings.LOGGING_LEVEL, settings.LOGGING_FORMAT)


def setup_routers(app: FastAPI) -> None:
    """Configure the application routers."""

    api_registry(app)


def setup_middlewares(app: FastAPI, settings: Settings) -> None:
    """Configure the application middlewares."""

    app.add_middleware(
        CORSMiddleware,
        allow_origins='*',
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """Configure the application exception handlers."""

    app.add_exception_handler(APIException, legacy_exception_handler)
    app.add_exception_handler(ProjectException, legacy_exception_handler)
    app.add_exception_handler(ServiceException, service_exception_handler)
    app.add_exception_handler(Exception, unexpected_exception_handler)


def legacy_exception_handler(request: Request, exception: APIException | ProjectException) -> JSONResponse:
    """Return backward compatible response structure for legacy exceptions."""

    return JSONResponse(status_code=exception.status_code, content=exception.content)


def service_exception_handler(request: Request, exception: ServiceException) -> JSONResponse:
    """Return the default response structure for service exceptions."""

    return JSONResponse(status_code=exception.status, content={'error': exception.dict()})


def unexpected_exception_handler(request: Request, exception: Exception) -> JSONResponse:
    """Return the default unhandled exception response structure for all unexpected exceptions."""

    logger.exception(  # noqa: G202
        f'Unexpected exception occurred while processing "{request.url}" url', exc_info=exception
    )

    return service_exception_handler(request, UnhandledException())


def setup_metrics(app: FastAPI, settings: Settings) -> None:
    """Instrument the application and expose endpoint for Prometheus metrics."""

    if not settings.ENABLE_PROMETHEUS_METRICS:
        return

    PrometheusFastApiInstrumentator().instrument(app).expose(app, include_in_schema=False)


def setup_tracing(app: FastAPI, settings: Settings) -> None:
    """Instrument the application with OpenTelemetry tracing."""

    if not settings.OPEN_TELEMETRY_ENABLED:
        return

    tracer_provider = TracerProvider(resource=Resource.create({SERVICE_NAME: settings.APP_NAME}))
    trace.set_tracer_provider(tracer_provider)

    otlp_exporter = OTLPSpanExporter(
        endpoint=f'{settings.OPEN_TELEMETRY_HOST}:{settings.OPEN_TELEMETRY_PORT}', insecure=True
    )

    tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()
