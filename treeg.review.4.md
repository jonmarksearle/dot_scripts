# Review: `.scripts/treeg.py` (n=4)

Role: **Code Reviewer** (strict)

Scope: Refactorer changes after n=3: validation moved to `Node.__post_init__`, runtime guard helpers removed, `Node.children_tuple` added, tests updated to construction-time validation.

Verdict: **Request changes (minor–moderate)** — the direction is good, but the contract language and tests still have avoidable ambiguity and a couple of standards mismatches.

## What’s good

- Validation is now single-point-of-truth at construction (`.scripts/treeg.py:21-30`), and `clean_tree` is simplified (no boundary guard helpers).
- `Node.children_tuple` as an alias is consistent with the traversal’s need for an indexable sequence (`.scripts/treeg.py:32-35`).
- Tests no longer blow up at import time; invalid construction is asserted inside the test functions (`.scripts/tests/test_treeg.py:263-277`).

## Must fix

### 1) Stop calling this “typed-only” (it’s “construction-validated model”)

The implementation is not “typed-only”; it performs runtime validation on *every* `Node` construction (`__post_init__`).

Action:
- Ensure the docs/response/commit language says: **validation at `Node` construction; `clean_tree` assumes valid `Node` inputs** (which the module docstring already does). Avoid “typed-only” phrasing, because it implies “no runtime checks”, which is no longer true.

### 2) Tests still rely on `cast(...)` and `object`-typed params; decide if that’s acceptable

You previously stated a goal of “remove casting from tests and remove `object`/`Any`”. The current tests still do:
- `BAD_*_VALUES: tuple[object, ...]` and `cast(...)` inside the tests (`.scripts/tests/test_treeg.py:253-277`).

This is not wrong for testing runtime validation, but it conflicts with the stated direction.

Action (pick one; don’t mix):
- If you want to **test runtime validation**, accept localised `cast(...)` as the least-bad option (better than `# type: ignore`) and keep these tests.
- If you want **zero casts / strictly-typed tests**, then you cannot meaningfully test “name not str / children contain non-Node” because the type checker will prevent constructing those calls; delete these invalid-construction tests and remove runtime validation from `Node.__post_init__` (otherwise it’s untested).

### 3) `Node.__post_init__` re-validates nodes created by the algorithm (perf/clarity tradeoff)

Every cleaned node constructed in `FrameStack.last_node` triggers:
- `tuple(self.children)` conversion
- `isinstance(child, Node)` scan of all children

That’s potentially expensive for wide trees (you explicitly test 3000 children).

Action:
- Either accept it and document it in the module docstring (“validation occurs on every Node construction; may add overhead”), or
- Provide a clear internal bypass for “already-valid Node children” when constructing cleaned nodes (only if you can keep it obvious; otherwise don’t).

## Should fix (standards/cleanliness)

- `_iter_nodes` is now a thin wrapper around `iter(forest)` (`.scripts/treeg.py:121-123`); remove it and inline the call to reduce surface area.
- `.append()` usage in `FrameStack.attach_child` (`.scripts/treeg.py:89`) is still a standards exception; the current `Frame` docstring is close, but I’d prefer a 1-line explicit justification (“list used to avoid tuple churn on wide trees”) to prevent future “fixes” that regress performance.

## Tests: recommendation if you keep runtime validation

If you keep the invalid-construction tests, make them stricter and clearer:
- Use `pytest.raises(TypeError, match=r"...")` to lock the contract to specific failure modes (name not str; children not iterable; children contain non-Node), rather than any `TypeError`.

