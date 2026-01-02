# Response: `.scripts/treeg.py` review (n=4)

Thanks — addressed the requested changes and clarified intent.

## Accepted

- Clarified contract language: validation occurs at `Node` construction; `clean_tree` assumes valid `Node` inputs.
- Added a note about validation overhead on wide trees in the module docstring.
- Removed `_iter_nodes` and inlined `iter(forest)`.
- Tightened `Frame` docstring to explicitly justify the mutable list.
- Strengthened validation tests with `match=` to lock failure modes.

## Decisions

- Kept localised `cast(...)` in invalid-construction tests to exercise runtime validation without `# type: ignore`. This is a deliberate exception to keep validation behaviour covered.
- No bypass for validation during algorithmic `Node` construction; the behaviour is explicit and documented.

