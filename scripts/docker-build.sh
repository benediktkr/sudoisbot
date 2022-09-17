#!/bin/bash

set -e

source ./scripts/docker.env

if [[ "$1" == "builder" ]] || [[ "$1" == "" ]]; then
    docker build --pull --target builder -t ${repo_name}_builder:${docker_tag} .
fi

if [[ "$1" == "final" ]] || [[ "$1" == "" ]]; then
    docker build --pull -t ${repo_name}:${docker_tag} .
fi
