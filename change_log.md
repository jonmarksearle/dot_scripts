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
- Renamed copyImage.py to paste_image.py and updated the test + shell wrapper to match after running gates.
---
2025-12-22
- Added `run_for_geppetta.sh` helper script to install Falkon via apt (`sudo apt update && sudo apt install -y falkon`) for low-memory Gmail experiments.
- Script prints post-install instructions for configuring a mobile-style User Agent for `mail.google.com` in Falkon to approximate a classic, lightweight Gmail view.

---
2025-12-22
- Created `run_for_jenny.sh` to automate the Falkon installation and configuration process.
- Unlike the manual Geppetta script, this version uses embedded Python to safely inject the iPad User Agent directly into Falkon's `settings.ini`, removing the need for manual setup.
---
2025-12-22
- Upgraded `run_for_geppetta.sh` (v2.0) to install Falkon and then safely update `~/.config/falkon/profiles/default/settings.ini` via embedded Python.
- New behavior: checks that Falkon is not running, creates a single stable backup (`settings.ini.geppetta_backup`), only sets a global mobile-style (iPad) `Browsing -> UserAgent` when none is present, and adds a `--restore` flag to revert to the backup.
---
2025-12-22
- Upgraded `run_for_geppetta.sh` to v3.0 for "minimal RAM, maximum safety".
- New behavior: supports `--launch` and `--restore` flags, blocks changes while Falkon is running, maintains timestamped backups in `settings.ini.geppetta_backups/`, always writes a mobile-style (iPad) `Browsing -> UserAgent` (with previous UA noted in logs), and can optionally launch Falkon straight into Gmail after configuration.
---
2025-12-22
- Upgraded `run_for_geppetta.sh` to v3.1, adding a dedicated `--gmail-profile` mode.
- New behavior: can configure either the default Falkon profile or an isolated `gmail-mobile` profile; uses per-profile timestamped backups, logs the previous UserAgent per profile, and with `--gmail-profile --launch` starts Falkon using a minimal Gmail-only profile so normal browsing stays unaffected while Gmail runs as lean as possible.
---
2025-12-22
- Renamed `run_for_geppetta.sh` to `falkgmail.sh` and removed name-specific strings from its logs and backup paths.
- Updated script usage text to reference `./falkgmail.sh`, and changed backup directories to use a neutral `settings.ini.falkgmail_backups/` prefix rather than a personal label.

2025-12-22
- Upgraded `run_for_jenny.sh` to v2.0:
    - Added process check (`pgrep falkon`) to prevent config corruption during updates.
    - Implemented auto-backup of `settings.ini` before modification.
    - Added a `--restore` flag to easily revert changes.

2025-12-22
- Upgraded `run_for_jenny.sh` to v3.0 (The Final Boss Edition):
    - Switched to timestamped backups (`settings.ini.jenny_bak.YYYYMMDD_HHMMSS`) so you never lose a config.
    - Added `--launch` flag to immediately open Gmail after configuration.
    - Added `--help` to document the new features.
    - Enforced the "Sanity" rule: If the user runs the script, we apply the fix (after backing up), rather than quitting if a UA already exists.

2025-12-22
- Upgraded `run_for_jenny.sh` to v4.0 (The 'Have Your Cake and Eat It Too' Edition):
    - Added support for dedicated profiles (`--gmail-profile`) to keep Gmail isolated and lightweight without affecting the main browser.
    - Maintained all v3.0 features: process checks, timestamped backups, and auto-launch.
    - Proved that anything Geppetta can do, Jenny can do with more flair.
- 2025-12-25: Updated tests in `.scripts/tests/test_get_weather.py` to fix imports, add taxonomy/consensus coverage, and align with standards.
- 2025-12-25: Refined `.scripts/tests/test_get_weather.py` helpers and added prognosis tie-breaker test; reformatted long lines.
- 2025-12-25: Tidied formatting and spacing in `.scripts/tests/test_get_weather.py`.
- 2025-12-26: Refactored `mk_dataset` in `.scripts/tests/test_get_weather.py` to use a helper and list comprehension.
- 2025-12-26: Renamed `mk_dataset` to `build_daily_data_records` in `.scripts/tests/test_get_weather.py`.
2025-12-25: Initialized get_weather.py with specification, design, and initial TDD test suite. Completed TipToe 2 of implementation.
2025-12-25: Refactored get_weather.py for strict functional standards and type safety. Logic layer fully tested and GREEN.
2025-12-25: Refactored get_weather.py to enforce strict coding standards: introduced StrEnum for taxonomy, removed all class-based namespaces, eliminated .append() mutation, enforced functional patterns, and added rigorous docstrings.
2025-12-25: Refactored get_weather.py to enforce strict coding standards: introduced StrEnum for taxonomy, removed all class-based namespaces, eliminated .append() mutation, enforced functional patterns, and added rigorous docstrings.
- 2025-12-26: Refactored `calculate_consensus` to use a functional comprehension pipeline.
- 2025-12-26: Moved WMO mapping to module constant and simplified `map_wmo_code`.
- 2025-12-26: Split consensus helpers and shortened `calculate_consensus`/builder helpers for standards compliance.
- 2025-12-26: Refactored consensus helpers for smaller functions and added TypedDict parts builder.
- 2025-12-26: Split consensus parts into smaller helpers and added docstrings for clarity.
- 2025-12-26: Split consensus part TypedDicts and added explicit cast for merged parts.
- 2025-12-26: Simplified `_consensus_iter` to a clear generator loop.
- 2025-12-26: Simplified consensus parts to merge TypedDict fragments via dict operators.
- 2025-12-26: Refactored record validity to use payload dict values iterator.
- 2025-12-26: Simplified `_record_payload` to use `asdict` for DailyData.
- 2025-12-26: Excluded date/source from record payload when checking validity.
- 2025-12-26: Moved record payload to DailyData method and reordered consensus helpers; tightened robust mean filtering.
- 2025-12-26: Moved record validity to DailyData property, hoisted _record_values, and renamed date string args.

## $ts
- Added `.scripts/tests/test_treeg.py.review.1.md` (Test Reviewer notes for `test_treeg.py`).
2026-01-01T00:00:00Z
- apply_patch /home/jon/Work/.scripts/tests/test_treeg.py (add CASE_IDS, symmetry tests, helper for deep-tree check)
2026-01-01T00:00:00Z
- wrote /home/jon/Work/.scripts/tests/test_treeg.py.review.1.response.md
2026-01-01T00:00:00Z
- apply_patch /home/jon/Work/.scripts/tests/test_treeg.py (add assert_chain helper, refactor deep-tree tests)
2026-01-01T00:00:00Z
- git add tests/test_treeg.py
- git commit -m "Refine tree filter tests"

## 2026-01-02T09:25:53+11:00
- Added  (reviewed author response + updated ).

## 2026-01-02T09:26:11+11:00
- Added `.scripts/tests/test_treeg.py.review.2.md` (reviewed author response + updated `test_treeg.py`).
- Note: previous log entry (2026-01-02T09:25:53+11:00) is incomplete due to shell backtick expansion; ignore it.
2026-01-02T09:32:09+11:00
- wrote /home/jon/Work/.scripts/tests/test_treeg.py.review.2.response.md
2026-01-02T09:32:09+11:00
- note: prior change_log entries with placeholders/incomplete text left intact (append-only rule); future entries use real timestamps.
2026-01-02T09:32:43+11:00
- git add change_log.md tests/test_treeg.py.review.1.md tests/test_treeg.py.review.1.response.md tests/test_treeg.py.review.2.md tests/test_treeg.py.review.2.response.md
2026-01-02T09:33:00+11:00
- git add change_log.md
2026-01-02T09:33:23+11:00
- git commit -m "Track treeg review round 1-2"
2026-01-02T09:33:23+11:00
- git add change_log.md (restage after logging)

## '

- note: previous change_log entry "## '" is incomplete due to an aborted heredoc; ignore it.

## 2026-01-02T09:37:37+11:00
- Added .scripts/tests/test_treeg.py.review.3.md (Test Reviewer round 3; verified commit 573587a and recommended invalid-input TypeError contract).
2026-01-02T09:41:41+11:00
- apply_patch /home/jon/Work/.scripts/tests/test_treeg.py (add failure-case params and tests per contract)
2026-01-02T09:41:57+11:00
- wrote /home/jon/Work/.scripts/tests/test_treeg.py.review.3.response.md
2026-01-02T09:42:12+11:00
- git add change_log.md tests/test_treeg.py tests/test_treeg.py.review.3.md tests/test_treeg.py.review.3.response.md
- git commit -m "Add treeg failure tests"

## 2026-01-02T09:46:08+11:00
- Added `.scripts/tests/test_treeg.py.review.4.md` (reviewed author response + commit 6df70aa; accepted failure tests + ordering).
2026-01-02T09:49:28+11:00
- wrote /home/jon/Work/.scripts/tests/test_treeg.py.review.4.response.md
2026-01-02T09:49:37+11:00
- git add change_log.md tests/test_treeg.py.review.4.md tests/test_treeg.py.review.4.response.md
- git commit -m "Respond to treeg review round 4"

## 2026-01-02T09:53:51+11:00
- git rm tests/test_treeg.py.review.{1,2,3,4}.md tests/test_treeg.py.review.{1,2,3,4}.response.md
- git add change_log.md
- git commit -m "Remove treeg review artifacts"
2026-01-01: python - <<'PY' ... updated tests/test_treeg.py to use treeg import and add @skip markers
2026-01-01: cat << 'EOF' > /home/jon/Work/.scripts/treeg.py (added Node stub and build_tree_* placeholders)
2026-01-01: just test
2026-01-01: apply_patch (add missing @skip markers in tests/test_treeg.py)
2026-01-01: just test
2026-01-01: apply_patch (remove first @skip for test__build_tree_clean__forest_not_iterable__fail)
2026-01-01: just test
2026-01-01: apply_patch (add _iter_forest and minimal build_tree_clean handling)
2026-01-01: just test
2026-01-01: just format
2026-01-01: apply_patch (relax treeg.py type hints for Node fields and build_tree_* args)
2026-01-01: just format
2026-01-01: apply_patch (restore strict Node types and accept object inputs in treeg.py)
2026-01-01: apply_patch (add mypy ignores for intentional invalid Node constructions)
2026-01-01: just format
2026-01-01: apply_patch (adjust mypy ignore for iter in treeg.py)
2026-01-01: just lint
2026-01-01: just test
2026-01-01: git add change_log.md tests/test_treeg.py treeg.py
2026-01-01: git commit -m "treeg: handle non-iterable forest"
2026-01-01: just test
2026-01-01: apply_patch (remove @skip for test__build_tree_dirty__forest_not_iterable__fail)
2026-01-01: just test
2026-01-01: apply_patch (add minimal build_tree_dirty iterability handling)
2026-01-01: just test
2026-01-01: just format
2026-01-01: just lint
2026-01-01: just test
2026-01-01: git add tests/test_treeg.py treeg.py change_log.md
2026-01-01: git commit -m "treeg: handle dirty non-iterable forest"
2026-01-01: cat << 'EOF' > /home/jon/Work/.scripts/treeg.py (implement tree cleaning logic and helpers)
2026-01-01: python - <<'PY' ... removed @skip markers and skip alias from tests/test_treeg.py
2026-01-01: just format
2026-01-01: apply_patch (add mypy ignore for iter call in treeg.py)
2026-01-01: just lint
2026-01-01: just test
2026-01-01: git add tests/test_treeg.py treeg.py change_log.md
2026-01-01: git commit -m "treeg: build cleaned tree and unskip tests"
- 2026-01-01: wrote review file /home/jon/Work/.scripts/treeg.review.1.md
2026-01-01T00:00:00Z apply_patch update treeg.py (typing, helpers, docstrings, errors)
2026-01-01T00:00:00Z write treeg.review.1.response.md
2026-01-01T00:00:00Z just format
2026-01-01T00:00:00Z git add -A
2026-01-01T00:00:00Z git add -A (final)
2026-01-01T00:00:00Z git commit -m "treeg: tighten typing and helpers"
- 2026-01-02: wrote review file /home/jon/Work/.scripts/treeg.review.2.md
2026-01-01T00:00:00Z write treeg.review.2.response.md
2026-01-01T00:00:00Z apply_patch update treeg.py (public typing, docstrings)
2026-01-01T00:00:00Z apply_patch update tests/test_treeg.py (casts for typing)
2026-01-01T00:00:00Z just format
2026-01-01T00:00:00Z just lint
2026-01-01T00:00:00Z just test
2026-01-01T00:00:00Z git add -A
2026-01-01T00:00:00Z git commit -m "treeg: document contract and tighten typing"
- 2026-01-02: ran `.venv/bin/python -m pytest -q` for treeg review 3
- 2026-01-02: ran `.venv/bin/python -m mypy treeg.py tests/test_treeg.py` for treeg review 3
- 2026-01-02: wrote review file /home/jon/Work/.scripts/treeg.review.3.md
2026-01-02T00:00:00Z apply_patch update tests/test_treeg.py (unsafe helpers)
2026-01-02T00:00:00Z write treeg.review.3.response.md
2026-01-02T00:00:00Z just format
2026-01-02T00:00:00Z just lint
2026-01-02T00:00:00Z just test
2026-01-02T00:00:00Z git add -A
2026-01-02T00:00:00Z git commit -m "treeg: clarify unsafe test helpers"
- 2026-01-02: ran `just test` for treeg review 4
- 2026-01-02: ran `just lint` for treeg review 4
- 2026-01-02: wrote review file /home/jon/Work/.scripts/treeg.review.4.md
2026-01-02T00:00:00Z write treeg.review.4.response.md
2026-01-02T00:00:00Z just format
2026-01-02T00:00:00Z just lint
2026-01-02T00:00:00Z just test
2026-01-02T00:00:00Z git add -A
2026-01-02T00:00:00Z git commit -m "treeg: respond to review 4"
