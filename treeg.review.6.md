# Code Review: treeg.py (review 6)

Role: Code Reviewer (strict)

## Summary
Request is clear: collapse the public API to a single entry point:

- Remove `build_tree_clean` and `build_tree_dirty`
- Add `build_tree(forest: Iterable[Node]) -> list[Node]`

This is a clarity win. It also requires docstring and test updates to avoid leaving “alias/clean-vs-dirty” artefacts behind.

## Required changes (action required)
1) **Replace the public API with `build_tree`.**
   - Remove `build_tree_clean` and `build_tree_dirty` entirely.
   - Add `build_tree(forest: Iterable[Node]) -> list[Node]` as the only public entry point.
   - Update the module docstring to remove any mention of `build_tree_dirty`/aliasing.

2) **Re-evaluate `_iter_forest` (keep only if it pulls its weight).**
   With the public signature narrowed to `Iterable[Node]`, you can simplify:
   - If you don’t care about a custom error message for non-iterables: delete `_iter_forest` and iterate `forest` directly (runtime misuse still raises `TypeError`).
   - If you do want a consistent message (and to keep the “non-iterable forest” runtime-guard tests meaningful): keep `_iter_forest`, but ensure its name/docstring make it clearly a *defensive runtime guard*.

3) **Align internal typing with the new contract.**
   - `_build_tree` should no longer take `forest: object` if the public contract is `Iterable[Node]`.
   - Prefer:
     - `def _build_tree(forest: Iterable[Node]) -> list[Node]: ...`
     - and keep element validation via `_ensure_node` (still needed for runtime guard tests using `_unsafe_forest`).

4) **Update tests to the new API and remove duplicate test surfaces.**
   - Replace imports/usages of `build_tree_clean`/`build_tree_dirty` with `build_tree`.
   - Remove the duplicated “clean” vs “dirty” test pairs; keep exactly one set.
   - Rename tests to `test__build_tree__...`.

## Docstrings (fresh-reader pass)
1) **Module docstring should teach the mental model in ~6–10 lines.**
   After removing the alias, the module docstring should cover:
   - what `build_tree` does (empty-name parents removed; descendants dropped)
   - why it is iterative (deep trees)
   - the output guarantee (fresh node construction)
   - what errors it raises for invalid inputs (TypeError for non-iterable forest, non-Node elements, invalid node shapes)

2) **Helper docstrings: keep only where invariants are non-obvious.**
   - The frame/stack helpers are legitimately “non-obvious logic”: multi-line docstrings are justified.
   - For self-explanatory helpers (`_validate_name`, `_ensure_node`), prefer either no docstring or a one-liner only if it adds meaning beyond the name.

## Optional improvements (nice to have)
- Consider whether the name `build_tree` is potentially misleading (it *cleans* as it builds). If you keep the name (as requested), the public docstring should make the “cleaning” behaviour impossible to miss.
