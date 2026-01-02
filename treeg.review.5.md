# Review: `.scripts/treeg.py` (n=5)

Role: **Code Reviewer** (strict)

Scope: Latest state after refactorer’s “treeg: clarify validation contract and tests” commit (validation in `Node.__post_init__`, `children_tuple` property, updated tests with `match=`).

Verdict: **Approve with notes**.

## What’s good (meets the agreed direction)

- Contract is now explicit and internally consistent:
  - module docstring + `clean_tree` docstring both state: validation at `Node` construction; `clean_tree` assumes valid `Node` inputs (`.scripts/treeg.py`).
- Validation is single-point-of-truth (`Node.__post_init__`) and tests assert it at construction time with `match=` (good: stable failure modes) (`.scripts/tests/test_treeg.py`).
- `Node.children_tuple` is a clean, trivial alias that matches the traversal’s need for an indexable sequence (`.scripts/treeg.py`).
- `Frame` docstring now explicitly justifies the mutable list (prevents accidental “optimisations” that create tuple churn) (`.scripts/treeg.py`).
- Wrapper `_iter_nodes` removal and `iter(forest)` inlining reduces surface area (`.scripts/treeg.py`).

## Notes / tradeoffs (accepted, but be conscious)

### 1) This is not “typed-only”; it’s “construction-validated model”

`Node.__post_init__` is runtime validation. That’s fine and now documented; just keep terminology consistent in future reviews/responses.

### 2) Runtime validation overhead is real on wide trees

`Node.__post_init__` always:
- materialises `children = tuple(self.children)`
- scans `children` for non-`Node`

You documented this overhead (good). It is still a deliberate performance tradeoff in exchange for strong invariants.

### 3) Casts in tests are now a justified exception

The invalid-construction tests use localised `cast(...)` and `object` values to exercise runtime validation branches. That’s coherent with “we validate at construction”, and better than `# type: ignore`.

If you ever want “no casts in tests”, the consequence is: either stop validating at runtime, or accept that those branches won’t be covered.

## Small suggestions (optional)

- Consider tightening error messages slightly (“children must be Node instances”) if you want clearer UX; tests currently match the shorter message, so change only if you want to update those matches intentionally.

