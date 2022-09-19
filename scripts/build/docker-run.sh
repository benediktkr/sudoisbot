#!/bin/bash

set -e

source ./scripts/docker.env

docker run --rm -it ${repo_name}:${docker_tag} $*
