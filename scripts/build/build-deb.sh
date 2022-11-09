#!/bin/bash

set -e

DEPS="-d python3.10"

pypoetry_venv_path=$(poetry env info -p)
version=$(poetry version -s)
pwd=$(pwd)


echo "pypoetry_venv_path: $pypoetry_venv_path"
echo "version: $version"


fpm \
    -a all \
    -t deb \
    $DEPS \
    -n ${REPO_NAME} \
    -v ${version} \
    --config-files /etc/systemd/system/sudoisbot@.service \
    --after-install deb/after-install.sh \
    -s dir \
    $pypoetry_venv_path \
    $pypoetry_venv_path=/usr/local/virtualenvs/${REPO_NAME} \
    $(pwd)/deb/etc/systemd/system/=/etc/systemd/system/

mv -v ${REPO_NAME}_*.deb dist/
