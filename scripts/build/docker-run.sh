#!/bin/bash

set -e

source ./scripts/build/docker.env

docker run --rm -it ${repo_name}:${docker_tag} $*
