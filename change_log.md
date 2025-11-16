2025-11-04
- Adjusted `.scripts/flines.py` `_child_pairs` to pass containment context to children instead of duplicating function names, restoring `just test` pass.
- Refined `_child_pairs` to only access `.name` on nodes that define it, keeping `just lint` (mypy) happy.
---
Time: 2025-11-12T00:49:11+11:00
Action: please commit all
Commands:
- git add -A
- git commit -m "chore: commit all changes (standards consolidation and symlinks)"
2025-11-16
- Added clipboard image tests (`tests/test_copyImage.py`) and implemented `.scripts/copyImage.py` via TDD.
- Extended dependencies (pillow) in `pyproject.toml`, regenerated `uv.lock`, and reran ruff/mypy/pytest.
---
2025-11-16
- Refactored `tests/test_copyImage.py` to enforce ≤5 line bodies via fixtures/helpers, covering failure, jpeg conversion, and success cases.
- Added supporting pytest fixtures (stdout buffer, fetchers, fixed time, payload helpers) without touching production code.
---
2025-11-16
- Removed `ClipboardImageError`, refactored command/fetch loops to avoid nested try blocks, and added `_load_image` helper.
- Updated tests to expect standard RuntimeError paths; reran ruff/mypy/pytest after each change.
---
2025-11-16
- Split `copy_clipboard_image` into `_clipboard_jpeg`, `_persist_image`, and `_announce_path` to remove nesting and shrink body size.
- Gates: ruff format/check, mypy, pytest.
---
2025-11-16
- Documented `copyImage.py` usage in README and new copyImage.md; mentioned clipboard backends, timestamped filenames, and exit codes.
- Gates (post-doc update): ruff check (python only), mypy, pytest.
---
2025-11-16
- Reworked `_run_first` to use `_command_result` helper + comprehension-driven flow, eliminating tuple appends and keeping functional style.
- Gates: ruff format/check, mypy, pytest.
---
2025-11-16
- Refined `read_clipboard_image` using `_fetch_result` helper and comprehension-driven flow.
- Gates: ruff format/check, mypy, pytest.
---
