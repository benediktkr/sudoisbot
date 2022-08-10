FROM python:3.9 as base
MAINTAINER Benedikt Kristinsson <benedikt@lokun.is>

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC
ENV TERM=xterm-256color

RUN useradd -u 1210 -ms /bin/bash sudoisbot && \
        apt-get update && \
        python3 -m pip install --upgrade pip

USER sudoisbot
WORKDIR "/home/sudoisbot"
ENV HOME="/home/sudoisbot"
ENV PATH="${HOME}/.local/bin:${PATH}"

FROM base as builder

RUN python3 -m pip install poetry && \
        mkdir $HOME/builder && \
        mkdir $HOME/builder/dist
WORKDIR $HOME/builder
COPY .flake8 poetry.lock pyproject.toml $HOME/builder/

# install dependencies with poetry and then freeze them in a file, so
# the final stage wont have to install them on each docker build
# unless they have changed
RUN poetry install --no-interaction --ansi --no-root && \
        poetry export --without-hashes > requirements.txt

COPY README.md $HOME/builder/
COPY sudoisbot $HOME/builder/sudoisbot/
COPY tests $HOME/builder/tests/

RUN poetry build --no-interaction --ansi
ENTRYPOINT ["poetry"]
