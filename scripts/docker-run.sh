#!/bin/bash

set -e

source ./docker/docker.env

docker run --rm -it ${repo_name}:${docker_tag} $*
