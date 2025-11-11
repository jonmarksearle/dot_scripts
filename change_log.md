2025-11-04
- Adjusted `.scripts/flines.py` `_child_pairs` to pass containment context to children instead of duplicating function names, restoring `just test` pass.
- Refined `_child_pairs` to only access `.name` on nodes that define it, keeping `just lint` (mypy) happy.
---
Time: 2025-11-12T00:49:11+11:00
Action: please commit all
Commands:
- git add -A
- git commit -m "chore: commit all changes (standards consolidation and symlinks)"
