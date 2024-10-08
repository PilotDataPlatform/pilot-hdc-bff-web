FROM docker-registry.ebrains.eu/hdc-services-image/base-image:python-3.10.14-v1 AS bff-image

ENV PYTHONDONTWRITEBYTECODE=true \
    PYTHONIOENCODING=UTF-8 \
    POETRY_VERSION=1.3.2 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false

ENV PATH="${POETRY_HOME}/bin:${PATH}"

RUN curl -o /usr/local/bin/mc https://dl.min.io/client/mc/release/linux-amd64/mc

RUN chmod +x /usr/local/bin/mc

RUN curl -sSL https://install.python-poetry.org | python3 -

COPY poetry.lock pyproject.toml ./
RUN poetry install --no-dev --no-root --no-interaction

COPY api ./api
COPY app ./app
COPY config.py .
COPY COPYRIGHT .
COPY models ./models
COPY poetry.lock .
COPY pyproject.toml .
COPY README.md .
COPY resources ./resources
COPY services ./services

RUN chown -R app:app /app
USER app

ENV PATH="/app/.local/bin:${PATH}"
ENV MINIO_USERNAME=minioadmin
ENV MINIO_PASSWORD=minioadmin
ENV MINIO_URL=http://minio.minio:9000
CMD ["sh", "-c", "mc alias set minio $MINIO_URL $MINIO_USERNAME $MINIO_PASSWORD && python -m app"]
