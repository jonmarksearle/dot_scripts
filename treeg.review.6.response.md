# Response: treeg.py review 6

Thanks for the review. Responses below.

## Accepted
1) Replace public API with `build_tree` only; remove `build_tree_clean`/`build_tree_dirty`.
2) Keep `_iter_forest` as a defensive guard with an explicit docstring.
3) Align internal typing to `Iterable[Node]` for `_iter_nodes`/`_build_tree`.
4) Update tests to target `build_tree` only and remove duplicate clean/dirty surfaces.
5) Refresh module docstring to describe the single-entry API and error behaviours.

## Pushback
None.
