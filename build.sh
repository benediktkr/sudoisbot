#!/bin/bash

set -e

# set the version in the script and use it for a docker tag too
# make this a makefile

if [ "$1" = "" ]; then
   version=$(grep "^version.*=" pyproject.toml | awk -F'"' '{print $2}')
else
    version=$1
    poetry version $version
fi

poetry build -f sdist
cp dist/sudoisbot-${version}.tar.gz dist/sudoisbot-latest.tar.gz

docker build -t sudoisbot .
docker tag sudoisbot benediktkr/sudoisbot:latest
docker tag sudoisbot benediktkr/sudoisbot:$version

docker push benediktkr/sudoisbot:latest
docker push benediktkr/sudoisbot:$version

#git add pyproject.toml
#git commit -m "verison bumped to $version"
