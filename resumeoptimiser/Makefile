.PHONY: install dev lint type-check test run

install:
	pip install -e ".[dev]"

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

lint:
	ruff check app tests

fmt:
	ruff format app tests

type-check:
	mypy app

test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v

test-cov:
	pytest tests/ --cov=app --cov-report=term-missing
