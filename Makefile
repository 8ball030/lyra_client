.PHONY: tests
tests:
	poetry run pytest tests -vv

fmt:
	poetry run black tests lyra samples
	poetry run isort tests lyra samples

lint:
	poetry run flake8 tests lyra samples

all: fmt lint tests

test-docs:
	echo making docs
