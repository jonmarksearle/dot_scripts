# Code Review: treeg.py (review 7)

Role: Code Reviewer (strict)

## Summary
Renaming the single public entry point from `build_tree` to `clean_tree` is the right move: the function’s primary behaviour is cleaning (dropping empty-name parents and their descendants), and “build” is misleading for a fresh reader.

This is a breaking API change unless you keep a compatibility alias.

## Required changes (action required)
1) **Rename the public API to `clean_tree`.**
   - In `treeg.py`, replace `def build_tree(...)` with `def clean_tree(forest: Iterable[Node]) -> list[Node]`.
   - Ensure the module docstring and public docstring refer to `clean_tree` (not “build”).

2) **Update tests to target `clean_tree` and rename test functions accordingly.**
   - `tests/test_treeg.py`: import `clean_tree` and rename `test__build_tree__...` → `test__clean_tree__...`.
   - Keep the same behavioural coverage (invalid forests, invalid nodes, deep tree, subtree dropping, fresh node construction).

3) **Decide (and document) whether `build_tree` remains as a compatibility alias.**
   Choose one, explicitly:
   - **Preferred (safer):** keep `build_tree` as a deprecated alias for one cycle.
     - Implementation should be a single source of truth:
       - either `build_tree = clean_tree` (and accept shared docstring), or
       - `def build_tree(...): """Deprecated alias for clean_tree."""; return clean_tree(forest)`.
     - Add one sentence to the module docstring noting deprecation and intended removal timeline.
   - **Acceptable (strict break):** remove `build_tree` entirely.
     - Then you must update all call sites in `.scripts` (tests already cover this repo) and accept external breakage.

## Fresh-reader docstring pass (required)
- **Module docstring:** currently good, but rewrite to lead with the public API name (`clean_tree`) and its behavioural contract (drop descendants; fresh node construction; iterative traversal; error cases).
- **Public function docstring:** ensure it says “clean” not “build”, and is explicit about subtree dropping and identity non-reuse.

## Non-issues
- Keeping `_iter_forest` as a defensive guard is still reasonable because tests intentionally bypass typing with `_unsafe_forest`.
