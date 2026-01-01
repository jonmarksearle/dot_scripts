# Code Review: treeg.py

Role: Code Reviewer (strict)

## Summary
The algorithm works for the provided tests and avoids recursion for deep trees, but it violates multiple CODE_STANDARDS rules (typing precision, no type ignore, function size/single responsibility, and public API docs). These need fixing before further changes.

## Blockers
None.

## Major issues
1) **Type hints are imprecise and require a type ignore.**
   - `treeg.py:16-20` uses `forest: object -> Iterable[object]` and includes `# type: ignore[call-overload]`.
   - `treeg.py:42-43` returns `Iterable[Node]` but is a generator.
   - Standards require precise return types (`Iterator[T]`), avoid `Any`, and avoid `# type: ignore`.
   - Fix: treat input as `Iterable[Node]` at the boundary, or check `isinstance(forest, Iterable)` and return `Iterator[object]` without ignores, with `Iterator[Node]` for `_iter_nodes`.

2) **Function size and responsibilities in `_clean_node` exceed limits.**
   - `treeg.py:60-74` is >10 executable lines and mixes validation, traversal, node construction, and attachment.
   - Standards: <10 lines, single responsibility, Never Nester.
   - Fix: split into named helpers (e.g., `_finalise_frame`, `_next_child`, `_pop_frame`) and keep `_clean_node` as a short orchestrator.

3) **Public API lacks docstrings for non-obvious names.**
   - `treeg.py:82-87` (`build_tree_clean`, `build_tree_dirty`) have no docstrings.
   - Names do not fully explain the contract or difference, especially since they currently do the same thing.
   - Fix: add one-line docstrings describing behaviour and expectations (including filtering empty names and returning new nodes).

## Minor issues
1) **Redundant validation.**
   - `_clean_node` calls `_validate_name` even though `_ensure_node` already validates in `_iter_nodes`.
   - Not wrong, but duplicative and adds noise.

2) **Exception messages are empty.**
   - All `TypeError` raises (`treeg.py:19-20`, `25`, `29-31`, `38-39`) omit context, which makes debugging harder.
   - Not required by tests, but helpful for clarity.

## Notes on tests
- The iterative approach is appropriate for the deep tree test.
- Returning a list is required by the test contract, so that preference break is acceptable; call it out in docstrings to make it explicit.

## Required changes (concise)
- Replace type-ignored `iter(forest)` with an `Iterable` check and return `Iterator` types.
- Split `_clean_node` into smaller helpers (≤10 lines each) with clear responsibilities.
- Add public docstrings for `build_tree_clean` and `build_tree_dirty`.

