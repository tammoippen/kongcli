THIS_FILE := $(lastword $(MAKEFILE_LIST))

include .testenv
export $(shell sed 's/=.*//' .testenv)

format:
	poetry run black .

statics:
	poetry run black --check .
	poetry run flake8
	poetry run mypy src

tests:
	poetry run pytest

docker:
	docker-compose up --force-recreate --renew-anon-volumes  --detach

ci:
	poetry install
	@$(MAKE) -f $(THIS_FILE) statics
	pytest -p no:sugar

coveralls:
	apt-get update && apt-get install -y git
	pip install coveralls
	coveralls

.PHONY: format statics tests ci docker
