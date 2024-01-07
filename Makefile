.PHONY: tests
tests:
	poetry run pytest tests -vv  --reruns 3 --reruns-delay 5

fmt:
	poetry run black tests lyra examples
	poetry run isort tests lyra examples

lint:
	poetry run flake8 tests lyra examples

all: fmt lint tests

test-docs:
	echo making docs
