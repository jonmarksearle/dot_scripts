test:
	PYTHONPATH=. uvx pytest

lint:
	uvx ruff check
	uvx mypy search.py browse.py tests/test_search.py tests/test_browse.py

format:
	uvx ruff format
