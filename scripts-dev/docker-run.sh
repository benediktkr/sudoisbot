#!/bin/bash

set -e

source ./scripts-dev/docker.env

docker run --rm -it ${docker_image_name}:${docker_tag} $*
