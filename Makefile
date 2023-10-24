.PHONY: tests
tests:
	pytest tests

fmt:
	black .
	isort tests lyra

lint:
	flake8 .