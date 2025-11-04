test:
	PYTHONPATH=. uvx pytest typer rich -- pytest

lint:
	uvx ruff check
	uvx mypy **.py

format:
	uvx ruff format
