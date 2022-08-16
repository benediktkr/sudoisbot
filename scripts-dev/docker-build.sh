#!/bin/bash

set -e

source ./scripts-dev/docker.env

echo
echo "repo: ${repo}"
echo "version: ${version}"
echo

docker build --pull --target builder -t ${repo}_builder:${version} .
docker build --pull -t ${docker_image_name}:${docker_tag} .
