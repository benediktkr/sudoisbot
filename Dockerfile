FROM python:3.9 as base
MAINTAINER Benedikt Kristinsson <ben@lokun.is>

ENV TZ=UTC
ENV DEBIAN_FRONTEND=noninteractive
ENV TERM=xterm-256color
ENV PIP_DISABLE_ROOT_WARNING=1

ENV REPO_NAME=sudoisbot
ENV USER_NAME=${REPO_NAME}
ENV UID=1337

ENV POETRY_CONFIG_DIR "${XDG_CONFIG_HOME}"
RUN env

RUN apt-get update && \
        apt-get autoremove && \
        apt-get autoclean && \
        python3 -m pip install --upgrade pip && \
        python3 -m pip cache purge && \
        useradd -u ${UID} -ms /bin/bash ${USER_NAME} && \
        mkdir -p /opt/${REPO_NAME} && \
        chown ${USER_NAME}. /opt/${REPO_NAME}

USER ${USER_NAME}
WORKDIR /opt/${REPO_NAME}
ENV PATH="/home/${USER_NAME}/.local/bin:${PATH}"

FROM base as builder

RUN python3 -m pip install poetry --pre && \
        python3 -m pip cache purge && \
        poetry self -V
COPY --chown=${USER_NAME} .flake8 poetry.lock pyproject.toml /opt/${REPO_NAME}/

# install dependencies with poetry and then freeze them in a file, so
# the final stage wont have to install them on each docker build
# unless they have changed
RUN poetry install --no-interaction  --no-root && \
        poetry export --without-hashes --output requirements.txt

COPY --chown=${USER_NAME} README.md /opt/${REPO_NAME}/
COPY --chown=${USER_NAME} sudoisbot /opt/${REPO_NAME}/sudoisbot/
COPY --chown=${USER_NAME} tests /opt/${REPO_NAME}/tests/
COPY --chown=${USER_NAME} poetry.toml /opt/${REPO_NAME}/

RUN poetry run pytest && \
        poetry run isort . --check > /tmp/isort.txt 2>&1 || true && \
        poetry run flake8 > /tmp/flake8.txt 2>&1 || true && \
        poetry config repositories.sudois && \
        poetry install --no-interaction

# building the python package here and copying the build files from it
# makes more sense than running the container with a bind mount,
# because this way we dont need to deal with permissions
RUN  poetry build --no-interaction

RUN "echo $POETRY_CONFIG_DIR"

ENTRYPOINT ["poetry"]
CMD ["build"]

FROM base as final
COPY --chown=${USER_NAME} --from=builder /opt/${REPO_NAME}/requirements.txt /opt/${REPO_NAME}/
RUN python3 -m pip install -r /opt/${REPO_NAME}/requirements.txt && \
        python3 -m pip cache purge && \
        python3 -m pip cache purge && \
        rm -v /opt/${REPO_NAME}/requirements.txt

COPY --chown=${USER_NAME} --from=builder /opt/${REPO_NAME}/dist /opt/${REPO_NAME}/dist/
# installing the wheel package because the sdist fails to install on vanilla pip because
# we're using the alpha version
RUN ls -1 /opt/${REPO_NAME}/dist && \
        python3 -m pip install /opt/${REPO_NAME}/dist/${REPO_NAME}-*.whl && \
        rm -vrf /opt/${REPO_NAME}/dist/


HEALTHCHECK --start-period=5s --interval=15s --timeout=1s \
        CMD ruok_${REPO_NAME}

ENTRYPOINT ['sudoisbot']
