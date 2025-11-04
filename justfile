test:
	PYTHONPATH=. uvx pytest

lint:
	uvx ruff check
	uvx mypy **.py

format:
	uvx ruff format
