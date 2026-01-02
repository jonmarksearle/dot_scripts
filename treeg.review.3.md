# Review: `.scripts/treeg.py` (n=3, updated again)

Role: **Code Reviewer** (strict)

Scope: Architect decision: remove helper-based runtime type checking (`_iter_forest`, `_validate_name`, `_valid_node`), move child normalisation to `Node` (as `@property children_tuple`), and validate via either `Node.__post_init__` (dataclass) or Pydantic.

Verdict: **Proceed with contract change**, but do it explicitly and consistently (docstring + tests + code must align).

## Update (typed-only choice confirmed)

You’ve now chosen: **strict typed-only contract + tests**.

That resolves the biggest source of churn: you no longer need “accepts `object` just to raise `TypeError`” helper guards, and the tests should stop using `cast(...)` to feed invalid runtime shapes into `clean_tree`.

Non-negotiable statement (to avoid refactorer ambiguity):
- `clean_tree(forest: Iterable[Node]) -> list[Node]` is defined only for *actual* `Node` instances constructed under normal typing (no cast-based “malicious inputs”).
- Therefore, the behaviour “raise `TypeError` for non-iterable forest / non-Node elements / invalid Node shapes encountered at runtime inside `clean_tree`” is **removed from the contract**.
- Consequently, `_iter_forest`, `_validate_name`, and `_valid_node` must be deleted (and not replaced with another boundary-check layer).

## Why “`_valid_node(value: object) -> Node` is crazy” is a reasonable objection

Agree with the core concern: a public API that claims to accept `Node` should not *actually* accept `object` just to raise `TypeError`. That pattern is appropriate at external boundaries (API/user input) but is noise for a small internal script, and it tends to metastasise into “defensive programming everywhere”.

However, the current tests *force* this awkwardness by intentionally bypassing typing (`cast(...)`) to feed invalid values into `clean_tree`. If you remove the runtime guards, the tests must stop doing that at the `clean_tree` boundary and instead test validation where you want it: **`Node` construction (or Pydantic model validation)**.

## Contract change (make it explicit)

You are choosing a different contract than the current one.

Today, the module promises “Raises TypeError for non-iterable forests, non-Node elements, and invalid Node shapes” (`.scripts/treeg.py:6-7`) and tests assert that behaviour.

Under the new direction (no helper-based runtime guards), you must update the contract to one of the following:

### Option A (recommended): “Valid `Node` instances only”

Contract:
- `Node(...)` validates its own invariants at construction time.
- `clean_tree(forest: Iterable[Node])` assumes it receives an iterable of valid `Node`s.
- Passing non-`Node` elements to `clean_tree` is programmer error; exception type/message is not guaranteed.

This aligns with your goal of removing `_valid_node(object)` style runtime validation and keeping “validation belongs to the model”.

### Option B: “Boundary validation via Pydantic”

Contract:
- `clean_tree` accepts a broader input (e.g. dicts or mixed items) and uses Pydantic to coerce/validate into `Node`.
- Raises are consistent at the boundary (Pydantic `ValidationError`), but you accept a new dependency and a different exception surface.

If you want strict runtime validation *without* `object`-typed guards, this is the most coherent path — but it is heavier for `.scripts` (no Pydantic dependency today).

## Key consequence: tests must move invalid construction inside tests (no import-time explosions)

If you validate in `Node.__post_init__`, then tests that currently create invalid nodes at import time must change.

Right now, invalid `Node(...)` values are created at module import (`.scripts/tests/test_treeg.py:271-278`). With `__post_init__` validation, pytest won’t even start; the module will fail to import.

Therefore:
- invalid node creation must happen inside test functions (or fixtures) so you can assert the exception with `pytest.raises(...)`.

## What to remove vs what to keep (and what that implies for tests)

### Remove (per your decision)

- `_valid_node`: remove entirely; do not replace it with another “accepts `object` and checks `isinstance`” helper at the `clean_tree` boundary.
- `_iter_forest`: remove; allow Python’s `TypeError` from `iter(forest)` to surface naturally if someone passes a non-iterable.
- `_validate_name`: remove; validate in `Node.__post_init__` (dataclass path) or by using Pydantic field validation (Pydantic path).

### Validate at the model boundary instead

If you want runtime validation, put it in exactly one place:
- `Node.__post_init__` (or Pydantic `model_validate`) is the single point of truth.
- `clean_tree` assumes its inputs are `Node` instances with valid invariants.

That is the only coherent way to avoid object-typed guard functions while still validating runtime data.

## `children_tuple` as a `Node` property

Be honest about what it does:

- If `Node.children` remains `tuple[Node, ...]`, then `children_tuple` is redundant (it returns `self.children`).
- If you want `Node` to accept broader child shapes and normalise them, that logic belongs in `__post_init__` (single point of truth), not a property that could be called repeatedly.

If you still want the property for readability, I will accept it only if:
- spelling is `children_tuple` (not `childern_tuple`), and
- it is a pure, O(1) accessor over already-normalised storage.

## Testing changes (specific, to avoid refactorer pushback)

This is the part that must change to match the new contract. Concretely, in `.scripts/tests/test_treeg.py`:

### 1) Replace “clean_tree runtime guard” tests with “Node construction” tests

Remove or rewrite these tests (they are asserting the old contract):
- `test__clean_tree__forest_not_iterable__fail`
- `test__clean_tree__forest_contains_non_node__fail`
- `test__clean_tree__children_contains_non_node__fail`
- `test__clean_tree__name_not_str__fail`

These are the four `pytest.raises(TypeError)` tests that must go under the typed-only contract.

Replace with construction-time validation tests (all invalid `Node` creation happens *inside* the test):

- `test__Node__name_not_str__fail`
  - `with pytest.raises(TypeError): Node(cast(str, 1), ())`
- `test__Node__children_not_iterable__fail`
  - `with pytest.raises(TypeError): Node("a", cast(tuple[Node, ...], 1))`
- `test__Node__children_contains_non_node__fail`
  - `with pytest.raises(TypeError): Node("a", cast(tuple[Node, ...], ("x",)))`
  - and/or `Node("a", cast(tuple[Node, ...], (None,)))`

Keep them tiny via `@pytest.mark.parametrize` (this also keeps the suite readable and aligned with the standards):
- Parametrise over “bad name” objects.
- Parametrise over “bad children shapes” objects.

### 2) Stop constructing invalid nodes at module import time

Currently the module-level constants `FORESTS_WITH_INVALID_CHILDREN` / `FORESTS_WITH_NON_STR_NAME` build invalid `Node(...)` values at import, which will break as soon as `Node.__post_init__` validates.

Instead of constants containing `Node(...)`, store *factories*:
- `INVALID_NODE_FACTORIES: tuple[Callable[[], None], ...]` (or similar)
- Each factory builds the invalid `Node(...)` inside the test.

This preserves pytest collection and keeps failures properly asserted.

### 3) Decide what (if anything) you want to guarantee about invalid `clean_tree` inputs

Under Option A (“valid Node instances only”), the most honest stance is:
- do not test behaviour for “forest contains non-Node” at runtime; it is programmer error.

If you still want a friendly error for that case, that reintroduces boundary checking in `clean_tree` (which conflicts with your stated goal). Pick one.

## Recommendation (clear path forward)

Given `.scripts` currently has no Pydantic dependency, I recommend Option A:
- Keep `Node` as a dataclass.
- Validate in `Node.__post_init__` (and normalise there if you expand accepted inputs).
- Update docstring to say validation happens on `Node(...)` construction; `clean_tree` assumes valid `Node`s.
- Update tests: move invalid-node-shape assertions to construction-time tests, and remove the “clean_tree validates arbitrary input” expectations.

This gives you “no helper-based runtime guards” while still having runtime validation, just in the right place for the chosen contract.

## Answer: `children_tuple` as a `Node` property (yes, do it)

Given `Node.children: tuple[Node, ...]` and Frame’s needs (stable ordering + index access), it is correct that the traversal requires an indexable sequence.

Recommendation under the typed-only contract:
- Delete `_children_tuple` completely.
- Add `Node.children_tuple` as a trivial alias:
  - `@property`
  - returns `tuple[Node, ...]`
  - does **no** validation or conversion (it should just return `self.children`)

Then in the traversal:
- `Frame.children` should be initialised from `node.children_tuple` (or directly from `node.children`; the property is mainly readability).
