test:
	uv run python -m pytest

lint:
	uv run ruff check
	uv run mypy **.py

format:
	uv run ruff format
