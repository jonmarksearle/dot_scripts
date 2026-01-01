# Test Review — `test_treeg.py`

## Scope

Review target: `.scripts/tests/test_treeg.py`

Standards applied:
- `/home/jon/Work/CODE_STANDARDS.md`
- `/home/jon/Work/Standards/CODE_STANDARDS.pytest.md`
- `/home/jon/Work/Standards/writing_tests.md`
- `/home/jon/Work/Standards/CODE_STANDARDS.new.md`

## Summary

Good behavioural coverage for “filter empty-name nodes” across a wide variety of trees via parametrisation, plus generator-input support and copy/immutability expectations.

Main gaps vs the standards:
- missing failure/edge-path tests (and failure-first ordering),
- at least one test significantly exceeds the “≤5 executable lines / no loops in tests” discipline.

## What’s good

- Clear unit naming convention (`test__{unit}__{case}__success`) is mostly followed.
- Broad, readable behavioural matrix via `@pytest.mark.parametrize` over `CASES`.
- Important interface seams are exercised:
  - accepts iterables/generators (not just concrete containers),
  - output is structurally equal but not the same object graph (copy semantics).
- Isolation is good (no filesystem/network/subprocess).

## Standards violations / must-fix

1) **Missing failure tests (and ordering)**

`CODE_STANDARDS.pytest.md` expects failure tests (exceptions) as first-class and ordered before success tests. This file has no `_fail` tests at all, and all tests are success tests.

Action:
- Add `_fail` cases for invalid inputs that are part of the contract (e.g., non-`Node` elements in the forest, `None`, wrong types for `children`, non-iterable forest). Use `pytest.raises(...)` with an explicit exception type.
- Put those failure tests before the success tests in the module.

If the contract is “garbage in, garbage out is undefined”, then document that in the production API and consider whether `_fail` tests are still warranted for obvious programmer errors.

2) **One test breaks the “tiny test” discipline**

`test__build_tree_clean__supports_very_deep_tree__success` uses a `while` loop and many assertions. This violates the local test standards (“≤5 executable lines”, avoid loops/conditionals inside tests; push complexity into fixtures/helpers/parametrisation).

Action (suggested reshape):
- Keep the deep-depth behaviour (“doesn’t blow recursion / handles depth N”) but express it with 1–2 assertions:
  - `out == [chain(depth)]` (compares full structure), plus optionally `out[0] is not root` to keep the copy-semantics signal.
- Consider parametrising depth (e.g., `[0, 1, 10, 1000, 5000]`) with `pytest.param(..., id="...")` so failures are readable.

## Improvements (should-fix)

- **Add symmetry for `build_tree_dirty`**
  - The “very deep tree” coverage and “excluded parent drops subtree” are currently only for `build_tree_clean`. If these functions are meant to be equivalent, mirror those tests for `build_tree_dirty`.

- **Tighten “one behaviour per test”**
  - The “returns_copy_not_same_objects” tests currently assert both equality and identity separation. Consider splitting:
    - one test asserts structural equality,
    - one test asserts identities differ (copy semantics),
  - so each test reads as one behavioural contract.

- **Add ids to the large parametrised suite**
  - `CASES` is extensive (which is fine), but without ids a failure is harder to interpret.
  - Use `pytest.param(..., id="single-empty")` style ids (or `ids=[...]`) so the failing case explains itself.

## Questions to confirm contract (blocks “proper” failure tests)

- What is the intended contract for invalid inputs?
  - Should `build_tree_*` raise `TypeError` on non-`Node` items / non-iterable forest?
  - Is `Node.name` always a `str` by construction, or do you want to defensively validate?

Answering those decides what the `_fail` test set should be.

