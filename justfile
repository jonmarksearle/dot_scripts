test:
	uv run python -m pytest

lint:
	ruff check
	mypy **/*.py

format:
	ruff format
	ruff check --fix
