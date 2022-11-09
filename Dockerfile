FROM python:3.10 as base
MAINTAINER Benedikt Kristinsson <ben@lokun.is>

ENV TZ=UTC
ENV DEBIAN_FRONTEND=noninteractive
ENV TERM=xterm-256color
# ENV PIP_ROOT_USER_ACTION=ignore
# can also use `pip install --root-user-action=ignore`

ENV REPO_NAME=sudoisbot
ENV USER_NAME=${REPO_NAME}
ENV UID=1337

RUN apt-get update && \
        apt-get autoremove && \
        apt-get autoclean && \
        useradd -u ${UID} -ms /bin/bash ${USER_NAME} && \
        mkdir -p /opt/${REPO_NAME} && \
        chown -R -v ${USER_NAME}. /opt/${REPO_NAME}

WORKDIR /home/${USER_NAME}
ENV PATH="/home/${USER_NAME}/.local/bin:${PATH}"

FROM base as builder
RUN apt-get update && \
        apt-get install -y ruby ruby-dev rubygems && \
        apt-get autoremove && \
        apt-get autoclean && \
        gem install --no-document fpm
USER ${USER_NAME}
ARG PIP_REPO_URL="https://git.sudo.is/api/packages/ben/pypi"
ARG PIP_REPO_NAME="gitea"
WORKDIR /opt/${REPO_NAME}

# --pre: enable installing pre-releases and dev-releases
RUN python3 -m pip install poetry --pre && \
        python3 -m pip cache purge && \
        python3 -m poetry config repositories.${PIP_REPO_NAME} ${PIP_REPO_URL} && \
        echo "repositories configured for poetry:" && \
        python3 -m poetry config repositories && \
        poetry self -V

#         python3 -m poetry config cache-dir "/usr/local/virtualenvs" && \

COPY --chown=${USER_NAME} .flake8 poetry.lock pyproject.toml /opt/${REPO_NAME}/

# install dependencies with poetry and then freeze them in a file, so
# the final stage wont have to install them on each docker build
# unless they have changed
RUN poetry install --no-interaction  --no-root && \
        poetry export --without-hashes --output requirements.txt

COPY --chown=${USER_NAME} README.md /opt/${REPO_NAME}/
COPY --chown=${USER_NAME} sudoisbot /opt/${REPO_NAME}/sudoisbot/
COPY --chown=${USER_NAME} tests /opt/${REPO_NAME}/tests/

RUN poetry run pytest && \
        poetry run isort . --check > /tmp/isort.txt 2>&1 || true && \
        poetry run flake8 > /tmp/flake8.txt 2>&1 || true && \
        poetry install --no-interaction

# building the python package here and copying the build files from it
# makes more sense than running the container with a bind mount,
# because this way we dont need to deal with permissions
RUN poetry build --no-interaction

COPY --chown=${USERNAME} deb /opt/${REPO_NAME}/deb/
COPY --chown=${USERNAME} scripts/build/build-deb.sh /usr/local/bin/build-deb.sh
RUN /usr/local/bin/build-deb.sh
RUN dpkg -I dist/sudoisbot_*.deb && dpkg -c dist/sudoisbot_*.deb


ENTRYPOINT ["poetry"]
CMD ["build"]

FROM base as final
USER ${USER_NAME}
COPY --chown=${USER_NAME} --from=builder /opt/${REPO_NAME}/requirements.txt /opt/${REPO_NAME}/
RUN python3 -m pip install -r /opt/${REPO_NAME}/requirements.txt && \
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

ENTRYPOINT ["sudoisbot"]
CMD []
