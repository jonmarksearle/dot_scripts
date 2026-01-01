# Test Review (Round 2) — `test_treeg.py`

Inputs considered:
- Author response: `.scripts/tests/test_treeg.py.review.1.response.md`
- Current file: `.scripts/tests/test_treeg.py`
- Project log: `.scripts/change_log.md`

## Outcome

Improved and closer to standards. Remaining blocker: **invalid-input failure contract is still undefined**, so `_fail` tests (and required failure-first ordering) are still missing.

## What changed (matches your response)

- Added `ids=...` for the large parametrised matrix (`CASE_IDS`). Good: makes failures interpretable.
- Refactored deep-tree test body to ≤5 lines via `assert_chain(...)`. Good: keeps the spec small and avoids recursive `__eq__` risk.
- Mirrored deep-tree and excluded-parent tests for `build_tree_dirty`. Good: symmetry.
- Kept copy-semantics tests focused on identity separation. Reasonable given `CASES` already covers structure.

## Standards check (pytests)

✅ **Parametrisation and ids**: good.

✅ **Test bodies ≤5 lines**: now compliant for the deep-tree path; helpers are an acceptable place for the loop.

⚠️ **Failure tests missing / ordering** (still): `CODE_STANDARDS.pytest.md` expects `_fail` tests and to place them before success tests. Your note is valid: we need a defined contract. This is now the only “must resolve” item.

## Contract decision needed (so `_fail` tests can be written)

Please pick the intended behaviour for each category; then the Test Author can add `_fail` tests and order them first:

1) Forest is not iterable (e.g. `None`, `1`): raise `TypeError`?
2) Forest contains non-`Node` items (e.g. `"x"`, `None`): raise `TypeError`?
3) `Node.children` contains non-`Node` items / wrong shape: raise `TypeError`?
4) Non-`str` names (if constructible): raise `TypeError`? (Or treat as “truthy/falsey” and only drop `""`?)

If you want “duck-typed” permissiveness, state it explicitly; otherwise I recommend `TypeError` for programmer misuse and tests to pin that down.

## Process note (from change log + repo state)

- `.scripts/change_log.md` contains literal placeholders like `## $ts` and multiple `2026-01-01T00:00:00Z` entries; if those are meant to be real timestamps, the logging command should write the actual time.
- Repo status shows the review files are untracked; confirm whether reviews/responses should be committed or intentionally left untracked.

