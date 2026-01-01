# Response — test_treeg.py.review.1

Agreements / changes applied
- Added readable ids for the parametrised CASES.
- Refactored the deep-tree test to keep the test body ≤5 lines; moved the loop into a small helper.
- Mirrored the deep-tree and excluded-parent tests for build_tree_dirty.
- Kept copy-semantics tests focused on identity separation; structural equality is already covered by the CASES matrix.

Pushback / needs clarification
- Failure tests: I can't add `_fail` tests without a defined contract for invalid inputs. Please confirm expected exceptions for non-Node elements, None, non-iterable forest, or invalid children types.
- Deep-tree equality: I avoided `out == [chain(depth)]` because `Node.__eq__` is likely recursive and could hit recursion limits at depth 5000; the helper asserts structure without recursion.
