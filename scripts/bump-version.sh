#!/bin/bash

set -e

poetry run python3 -m poetry version $*
