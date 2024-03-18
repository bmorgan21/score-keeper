FROM mcr.microsoft.com/devcontainers/python:0-3.11 as base

ENV PORT 8080
ENV PYTHONUNBUFFERED 1
ENV QUART_APP score_keeper
EXPOSE $PORT

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends postgresql-client


#---
FROM base as dev
ENV QUART_ENV development
ENV QUART_DEBUG true

RUN echo "alias init='source ~/venv/bin/activate'" > /home/vscode/.bash_aliases

ARG VENV_PATH="/home/vscode/venv"

COPY requirements.lock /tmp/pip-tmp/
RUN su vscode -c "python -m venv ${VENV_PATH}" \
    && ${VENV_PATH}/bin/pip install -r /tmp/pip-tmp/requirements.lock \
    && rm -rf /tmp/pip-tmp

#---
FROM base as prod
ENV APP_HOME /app
ENV QUART_ENV production

ARG VENV_PATH="/venv"

COPY requirements.lock /tmp/pip-tmp/
RUN python -m venv ${VENV_PATH} \
    && ${VENV_PATH}/bin/pip install -r /tmp/pip-tmp/requirements.lock \
    && rm -rf /tmp/pip-tmp

WORKDIR $APP_HOME

COPY . .

CMD exec /venv/bin/hypercorn --bind :$PORT $QUART_APP:app
