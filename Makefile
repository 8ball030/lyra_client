.PHONY: tests
tests:
	pytest tests -vv

fmt:
	black .
	isort tests lyra

lint:
	flake8 .