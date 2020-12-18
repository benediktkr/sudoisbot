SHELL=/bin/bash

NAME=$(shell basename $(CURDIR))
POETRY_VERSION=$(shell poetry version)
NAMESIZE=$(shell ${#NAME})
VERSION=$(shell echo ${POETRY_VERSION:8} )

build: poetry-build docker-build docker-tag

poetry-build:
	poetry build ${VERSION}

docker-build:
	docker build -t sudoisbot .

docker-tag:
	docker tag sudoisbot benediktkr/sudoisbot:latest
