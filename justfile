test:
	PYTHONPATH=. uvx pytest typer rich

lint:
	uvx ruff check
	uvx mypy **.py

format:
	uvx ruff format
