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
	poetry install
	@$(MAKE) -f $(THIS_FILE) statics tests


.PHONY: format statics tests ci
