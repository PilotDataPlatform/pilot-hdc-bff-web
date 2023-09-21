FROM python:3.9-buster


ENV PYTHONDONTWRITEBYTECODE=true \
    PYTHONIOENCODING=UTF-8 \
    POETRY_VERSION=1.3.2 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false

ENV PATH="${POETRY_HOME}/bin:${PATH}"

RUN groupadd --gid 1004 deploy \
    && useradd --home-dir /home/deploy --create-home --uid 1004 \
        --gid 1004 --shell /bin/sh --skel /dev/null deploy
WORKDIR /home/deploy
RUN wget https://dl.min.io/client/mc/release/linux-amd64/mc -P /usr/local/bin

RUN chmod +x /usr/local/bin/mc

RUN apt-get update && apt-get install libsasl2-dev python-dev libldap2-dev libssl-dev -y && rm -rf /var/lib/apt/lists/*
RUN curl -sSL https://install.python-poetry.org | python3 -

COPY poetry.lock pyproject.toml ./
RUN poetry install --no-dev --no-root --no-interaction

USER root
COPY .  ./
RUN chown -R deploy:deploy /home/deploy

USER deploy
ENV PATH="/home/deploy/.local/bin:${PATH}"
ENV MINIO_USERNAME=minioadmin
ENV MINIO_PASSWORD=minioadmin
ENV MINIO_URL=http://minio.minio:9000
CMD ["sh", "-c", "mc alias set minio $MINIO_URL $MINIO_USERNAME $MINIO_PASSWORD && python -m app"]
