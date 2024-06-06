# Dockerfile: Is a text file that contains instructions, at times called commands or directives, which dictate how to create a docker image (configuration files and shell scripts)

# Image: is a read-only template with instructions for creating a Docker container. Often, an image is based on another image, with some additional customizaztion

# Container: A container is a runnable instance of an image. You can create, start, stop, move, or delete a container using the docker api

# Multi-stage builds: is a feature in Docker which allows you to create a smaller image by using multiple stages in the build process. This is useful when you have a build process that requires a lot of dependencies, but you only need the final output

# 1. Build dependencies wheels
# 2. Run application

ARG PYTHON_VERSION=3.11.5-bullseye

FROM python:${PYTHON_VERSION} as python


FROM python as python-build-stage
ARG BUILD_ENVIRONMENT=local

# execute shell commands during image building
# install packages, setup environments, configure the system, etc
RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential \
    libpq-dev

COPY ./requirements .

RUN pip wheel --wheel-dir /usr/src/app/wheels \
    -r ${BUILD_ENVIRONMENT}.txt
# A wheel is a built package that can be installed quickly without needing to compile any source code. Wheels have a .whl extension.

FROM python as python-run-stage
ARG BUILD_ENVIRONMENT=local

ARG APP_HOME=/app

# avoid creating pyc files (bytecode files that are created by Python and read by the interpreter) so it doesn't waste disk space
ENV PYTHONDONTWRITEBYTECODE 1

# make sure Python writes output immediately (unbuffered output)
ENV PYTHONUNBUFFERED 1

ENV BUILD_ENV ${BUILD_ENVIRONMENT}

WORKDIR ${APP_HOME}

RUN apt-get update && apt-get install --no-install-recommends -y \
    libpq-dev \
    gettext \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*

COPY --from=python-build-stage /usr/src/app/wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/* \
    && rm -rf /wheels/

COPY ./docker/local/django/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint

COPY ./docker/local/django/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

COPY . ${APP_HOME}

ENTRYPOINT [ "/entrypoint" ]