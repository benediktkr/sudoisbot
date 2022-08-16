FROM python:3.9 as base
MAINTAINER Benedikt Kristinsson <benedikt@lokun.is>

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC
ENV TERM=xterm-256color

ENV REPO_NAME=sudoisbot
ENV USER_NAME=${REPO_NAME}
ENV UID=1337

RUN apt-get update && \
        apt-get autoremove && \
        apt-get autoclean && \
        python3 -m pip install --upgrade pip && \
        python3 -m pip cache purge

RUN useradd -u ${UID} -ms /bin/bash ${USER_NAME} && \
        mkdir -p /opt/${REPO_NAME} && \
        chown ${USER_NAME}. /opt/${REPO_NAME}

USER ${USER_NAME}
WORKDIR /opt/${REPO_NAME}
ENV PATH="/home/${USER_NAME}/.local/bin:${PATH}"

FROM base as builder

RUN python3 -m pip install poetry --pre && \
        python3 -m pip cache purge && \
        poetry self -V
COPY .flake8 poetry.lock pyproject.toml /opt/${REPO_NAME}/

# install dependencies with poetry and then freeze them in a file, so
# the final stage wont have to install them on each docker build
# unless they have changed
RUN poetry install --no-interaction --ansi --no-root && \
        poetry export --without-hashes --output requirements.txt

COPY README.md /opt/${REPO_NAME}/
COPY sudoisbot /opt/${REPO_NAME}/sudoisbot/
COPY tests /opt/${REPO_NAME}/tests/

RUN poetry run pytest
RUN poetry run isort . --check > /tmp/isort.txt 2>&1 || true
RUN poetry run flake8 > /tmp/flake8.txt 2>&1 || true

RUN poetry install --no-interaction --ansi

# building the python package here and copying the build files from it
# makes more sense than running the container with a bind mount,
# because this way we dont need to deal with permissions
RUN poetry build --no-interaction --ansi

ENTRYPOINT ["poetry"]
CMD ["build"]

FROM base as final
COPY --from=builder /opt/${REPO_NAME}/requirements.txt /opt/${REPO_NAME}/
RUN python3 -m pip install -r /opt/${REPO_NAME}/requirements.txt && \
        python3 -m pip cache purge && \
        rm -v /opt/${REPO_NAME}/requirements.txt

HEALTHCHECK --start-period=5s --interval=15s --timeout=1s \
        CMD ruok_${REPO_NAME}

ENTRYPOINT ['sudoisbot']
