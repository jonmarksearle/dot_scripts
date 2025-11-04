test:
	PYTHONPATH=. uvx pytest

lint:
	uvx ruff check
	uvx mypy

format:
	uvx ruff format
