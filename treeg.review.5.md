# Code Review: treeg.py (review 5)

Role: Code Reviewer (strict)

## Summary
Code is correct, tested, and typed, but readability is still below the “obvious intent” bar due to under-documented internal invariants.

Your note is valid: several helpers are not self-explanatory without knowing the stack/frame representation. Per `CODE_STANDARDS.new.md` docstring rules: prefer names that encode intent; use one-line docstrings by default; use multi-line docstrings only when the logic/invariants are non-obvious (this module qualifies).

Verification in `/home/jon/Work/.scripts`:
- `just lint` passes

## Major issues (action required)
1) **Add a module docstring describing the algorithm and invariants.**
   - `treeg.py:1` has no module docstring.
   - Required content (prefer short; multi-line is acceptable here because invariants are non-obvious):
     - Purpose: “clean a forest of Node by removing empty-name nodes; if a parent is removed, drop descendants”.
     - Non-recursive traversal rationale (deep trees; avoids recursion limit).
     - Output guarantees: fresh nodes, no identity reuse.
     - Why `build_tree_dirty` exists (alias for compatibility/teaching).

2) **Document the `Frame` representation and the stack transition functions.**
   - `treeg.py:7` defines `type Frame = tuple[Node, tuple[object, ...], int, tuple[Node, ...]]`.
   - The meaning is not obvious, and the tuple-of-tuples shape is a high cognitive load.
   - Required: either
     - (preferred) replace `Frame` with a `@dataclass(frozen=True, slots=True)` (self-documenting field names), OR
     - add docstrings to at least `_initial_stack` (`treeg.py:59-60`), `_step_stack` (`treeg.py:79-85`), `_pop_frame` (`treeg.py:70-76`), and `_finalise_frame` (`treeg.py:63-67`) describing (multi-line acceptable here because logic is non-obvious):
       - what each frame field means
       - what invariants hold (e.g., `index` is “next child index to process”, `cleaned` holds already-cleaned children)
       - what conditions produce a `built` node vs `None`

## Minor issues (recommended)
1) **Add docstrings to test “unsafe” helpers.**
   - `tests/test_treeg.py:32-41` helpers are good, but should have one-line docstrings explaining they intentionally bypass static typing to test runtime guards.
   - These helpers are a pattern worth reusing; document intent once so future readers don’t assume they are normal casts.

2) **Clarify TypeError message context (optional).**
   - Current messages are okay, but some are generic:
     - `treeg.py:28-29` “expected Node” could include the received type.
     - `treeg.py:24` “node name must be str” could include `type(node.name)`.
   - This is optional because tests don’t require it, but it materially improves diagnosability.

## Non-issues
- Prefer one-line docstrings; multi-line is appropriate here because the frame/stack invariants are non-obvious.
- The alias explanation for `build_tree_dirty` is now explicit and acceptable.
