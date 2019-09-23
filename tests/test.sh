#! /bin/sh
set -x

# meant for running in the docker image / ci
apk add --no-cache build-base  # typed-ast
poetry install
poetry run black --check .
poetry run flake8
poetry run mypy src
poetry run pytest
