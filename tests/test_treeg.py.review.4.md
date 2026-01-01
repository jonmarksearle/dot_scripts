# Test Review (Round 4) — `test_treeg.py`

Inputs considered:
- Author response: `tests/test_treeg.py.review.3.response.md`
- Commit: `6df70aa` (“Add treeg failure tests”)
- Current file: `tests/test_treeg.py`

## Outcome

Accepted.

You addressed the prior blocker by explicitly adopting the invalid-input contract and then adding `_fail` coverage and failure-first ordering.

## What’s good

- ✅ Contract is now explicit and consistent: invalid inputs raise `TypeError`.
- ✅ `_fail` tests exist for all four agreed categories and appear before success tests.
- ✅ Test bodies remain within the ≤5 executable-line discipline (parametrisation + simple `pytest.raises` blocks).
- ✅ Symmetry preserved across `build_tree_clean` and `build_tree_dirty`.
- ✅ Param ids are present for both success matrix (`CASE_IDS`) and failure matrices.

## Minor notes (optional)

- `FORESTS_WITH_NON_STR_NAME` / invalid-children cases assume `Node(...)` construction itself does not raise. If `Node` ever adds runtime validation in `__post_init__`, these tests may need to construct “bad nodes” differently (e.g., via a factory inside the `raises` context, or by targeting the constructor contract instead).
- If you want to reduce repetition between `clean` and `dirty` failure tests, you could parametrise over the function under test (`build_tree_clean`/`build_tree_dirty`) while keeping the body tiny. Not required.

## Next step

Nothing further required for this review series; proceed with normal quality gates (`just test` at minimum) as you integrate.

