THIS_FILE := $(lastword $(MAKEFILE_LIST))

format:
	black .

statics:
	black --check .
	flake8
	mypy src

tests:
	pytest

ci:
	apt-get update && apt-get install -y build-essential  # typed-ast
	poetry install
	@$(MAKE) -f $(THIS_FILE) statics tests


.PHONY: format statics tests ci
