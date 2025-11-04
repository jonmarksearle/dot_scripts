2025-11-04
- Adjusted `.scripts/flines.py` `_child_pairs` to pass containment context to children instead of duplicating function names, restoring `just test` pass.
- Refined `_child_pairs` to only access `.name` on nodes that define it, keeping `just lint` (mypy) happy.
