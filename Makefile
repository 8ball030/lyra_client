.PHONY: tests
tests:
	poetry run pytest tests -vv

fmt:
	poetry run black tests lyra 
	poetry run isort tests lyra

lint:
	poetry run flake8 tests lyra

all: fmt lint tests

test-docs:
	echo making docs
