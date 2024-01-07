.PHONY: tests
tests:
	poetry run pytest tests -vv  --reruns 10 --reruns-delay 20

fmt:
	poetry run black tests lyra examples
	poetry run isort tests lyra examples

lint:
	poetry run flake8 tests lyra examples

all: fmt lint tests

test-docs:
	echo making docs
