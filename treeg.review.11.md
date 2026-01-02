# Code Review: treeg.py (review 11)

Role: Code Reviewer (strict)

Scope note: peer comments about `treeg.alt.py` are ignored; it is out of scope.

## Summary
I agree with both peer reviewers’ main conclusion: `treeg.py` is now robust, library-safe (no global side effects), and scales to pathological depth and width.

The two real algorithmic hazards that mattered for the stated purpose are resolved:
- deep-chain stack churn (tuple-stack copying) → fixed via in-place `list` stack
- wide-node child accumulation churn (tuple growth) → fixed via per-frame `list[Node]` and tuple materialisation at finalisation

Verification in `/home/jon/Work/.scripts`:
- `just lint` passes
- `just test` passes (135 tests)

## Accepted changes
1) **True linear accumulation for children.**
   - Frame now uses `cleaned: list[Node]` and `_attach_child` appends in place.
   - `_finalise_frame` materialises `tuple(cleaned)` once.

2) **Regression coverage added for wide trees.**
   - `tests/test_treeg.py` includes `test__clean_tree__very_wide_root__success` (3000 children). This directly guards the previously identified O(k²) growth.

## Remaining issues
None required.

## Optional refinements (only if they improve clarity)
1) **`_children_tuple` is defensive; decide whether to keep it and say why.**
   - Today `Node.children` is typed as `tuple[Node, ...]`, so `tuple(node.children)` is usually a no-op.
   - However, your tests explicitly allow malformed runtime shapes (via `cast` helpers), and the module docstring promises a `TypeError` for non-iterable children. In that world, `_children_tuple` is not “theatre”; it’s an explicit boundary.
   - Recommendation: keep it as-is, but consider a one-line docstring (or a short note in the module docstring) that it exists to enforce runtime shape contracts even when type hints suggest the shape is already correct.

2) **Do not tighten `Frame`’s `children` element type unless you change validation strategy.**
   - A peer suggestion was to change `tuple[object, ...]` to `tuple[Node, ...]`.
   - With “validate on visit” and tests that inject non-`Node` children, `tuple[object, ...]` is the accurate type. Tightening it without validating elements up-front would be misleading.

3) **Complexity note (optional).**
   - If you want to document this as the canonical implementation, adding a brief “linear in number of nodes; no recursion depth limits” note to the module docstring is reasonable.
