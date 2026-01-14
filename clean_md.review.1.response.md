# Response: clean_md.py review n=1

Accepted
- Shifted intermediate pipelines to iterators and materialised only where slicing is needed.
- Adjusted `_split_related` to accept `Iterable[str]` and materialise internally.

Pushback
- None.

Changes implemented
- `_normalise_lines`, `_filter_lines`, `_take_until_related_marker` now return iterators.
- `_split_related` accepts `Iterable[str]` and materialises once.
- `_clean_lines` now materialises only at the header-splitting edge.
