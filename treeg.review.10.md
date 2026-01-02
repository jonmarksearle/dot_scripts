# Code Review: treeg.py (review 10)

Role: Code Reviewer (strict)

Scope note: `treeg.alt.py` is out of scope for this review.

## Summary
The fixes described by the author are present and materially improve the implementation:
- The stale `build_tree` alias claim is removed from the module docstring.
- The traversal stack is now a `list[Frame]` updated in place, eliminating the deep-chain O(d²) tuple-copy behaviour.
- Docstrings are clearer and match the current contract/control flow.

I re-read this in light of two additional peer reviews. One reviewer considers this “ship it” quality; another correctly points out there is still a worst-case quadratic behaviour for *very wide* nodes. Given our standards (principles > preferences), I’m upgrading that from “optional” to “recommended before calling this canonical/scalable”.\n+
Verification in `/home/jon/Work/.scripts`:
- `just lint` passes
- `just test` passes (134 tests)

## Accepted changes
1) **Docstring correctness fixed.**
   - `treeg.py:1-8` no longer claims a `build_tree` alias exists.

2) **Deep-chain performance foot-gun removed.**
   - The stack update is now in-place (`treeg.py:55-66`, `treeg.py:94-106`, `treeg.py:108-121`), which resolves the quadratic stack-copying issue flagged in review 9.
   - This is an acceptable standards tradeoff: local mutation improves correctness-for-real-inputs and keeps the algorithm’s intent obvious.

3) **Public contract docstring is now “fresh reader” friendly.**
   - `clean_tree` explicitly states forest input, subtree dropping, identity non-reuse, and TypeError conditions (`treeg.py:138-146`).

## Remaining issues
1) **Worst-case quadratic behaviour remains for very wide nodes (recommended fix).**
   - Even after switching the *stack* to a list, `_attach_child` still grows `cleaned` via tuple concatenation (`treeg.py:59`): `(*cleaned, child)`.
   - For a node with `k` kept children, that is O(1+2+…+k) tuple copying → O(k²) time/allocations for that node. A “star” tree (one root with many children) is the pathological case.
   - Recommended: store `cleaned` as a `list[Node]` in the frame, `.append()` in `_attach_child`, and convert to `tuple` in `_finalise_frame`. This is a justified preference break (local mutation buys real algorithmic improvement and typically improves clarity).

2) **Do not “tighten” `Frame.children` to `tuple[Node, ...]` unless you also change validation strategy.**
   - A peer suggestion was to change `Frame` from `tuple[object, ...]` to `tuple[Node, ...]`.
   - With the current design (validate each child when visited, and tests that deliberately smuggle non-`Node` children), `tuple[object, ...]` is accurate.
   - If you want `tuple[Node, ...]`, then `_children_tuple` must also validate/coerce elements (which may be a fine change, but it’s a behaviour/complexity shift).

## Optional follow-ups
- Consider adding a brief complexity note to the module or public docstring once the `cleaned`-as-list change lands (e.g., “linear in number of nodes; no recursion depth limits”).
