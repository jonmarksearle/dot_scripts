# Test Review (Round 3) — `test_treeg.py`

Inputs considered:
- Author response: `tests/test_treeg.py.review.2.response.md`
- Project log: `change_log.md`
- Commit: `573587a` (“Track treeg review round 1-2”)

## Verified author actions

- ✅ Wrote `tests/test_treeg.py.review.2.response.md`.
- ✅ Appended corrective notes + command logs to `change_log.md` (append-only honoured).
- ✅ Added/committed review + response files in `573587a`.
- ✅ `tests/test_treeg.py` is unchanged in `573587a` (consistent with “contract still undefined”).

## Review

Your response is accepted: deferring `_fail` tests until the invalid-input contract is defined is the correct move.

Tracking and committing the review/response artefacts is also accepted (keeps the repo state clean and makes the review trail durable).

## Required decision (so testing can proceed)

To unblock the required `_fail` tests and failure-first ordering, I recommend this contract:

1) Non-iterable forest (`None`, `1`) → **raise `TypeError`**
2) Forest contains non-`Node` items (`"x"`, `None`) → **raise `TypeError`**
3) `Node.children` contains non-`Node` items → **raise `TypeError`**
4) Non-`str` names → **raise `TypeError`**

And keep the existing behavioural rule for filtering as:
- exclude nodes whose `name == ""` (exact empty string only),
- keep `" "` and `"0"` (already covered in CASES).

If you want a more permissive, duck-typed API, state that explicitly; otherwise `TypeError` is the clearest “programmer misuse” signal and gives us strict `_fail` tests.

## Next required test changes (once contract is confirmed)

- Add `_fail` tests (ordered before all success tests) for each of the 4 categories above using `pytest.raises(TypeError)`.
- Keep each test body ≤5 executable lines via parametrisation.
- After adding `_fail` tests, reorder the module so failures come first.

