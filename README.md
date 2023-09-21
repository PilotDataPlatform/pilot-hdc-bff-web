# Backend for Frontend

[![Python](https://img.shields.io/badge/python-3.7-brightgreen.svg)](https://www.python.org/)

## About

The BFF is a proxy layer to allow easy access to the pilot microservices from a frontend application. BFF will handling calling the correct APIs to check permissions before calling the microservices.

## Built With
 - [FastAPI](https://fastapi.tiangolo.com/): Async API framework
 - [poetry](https://python-poetry.org/): python package management
 - [docker](https://docker.com)


# Getting Started

## Prerequisites

 1. The project is using poetry to handle the package. **Note here the poetry must install globally not in the anaconda virtual environment**

 ```
 pip install poetry
 ```

 ## Installation

 1. git clone the project:
 ```
 git clone git@github.com:PilotDataPlatform/bff-web.git
 ```

 2. install the package:
 ```
 poetry install
 ```

 3. create the `.env` file from `.env.schema`

 4. run it locally:
 ```
 poetry run python -m app
 ```

## Running with Docker

Add environment variables listed in .env.schema in the docker-compose.yaml file.

Start API with docker-compose:
```
docker-compose build
docker-compose up
```

## Urls
Port can be configured with the environment variable `PORT`
- API: http://localhost:5063
- API docs: http://localhost:5063/v1/api-doc

## Run tests

```
poetry run pytest
```

## Acknowledgements
The development of the HealthDataCloud open source software was supported by the EBRAINS research infrastructure, funded from the European Union's Horizon 2020 Framework Programme for Research and Innovation under the Specific Grant Agreement No. 945539 (Human Brain Project SGA3) and H2020 Research and Innovation Action Grant Interactive Computing E-Infrastructure for the Human Brain Project ICEI 800858.
