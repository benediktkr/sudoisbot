#!/bin/bash

set -e

git tag v$(poetry version -s)

read -p "push tag? " pushtag
case $pushtag in
    n|no|N|NO)
        echo "not pushing!"
        exit 0
        ;;
    *)
        echo -n
esac

git push --tags
