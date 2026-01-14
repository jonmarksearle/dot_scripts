# Code Review: clean_md.py (n=1)

Findings (priority order)

1) Prefer iterators over tuples for intermediate pipelines.
   - `_normalise_lines`, `_filter_lines`, and `_take_until_related_marker` materialise tuples even though their results are immediately consumed.
   - Standards prefer iterator pipelines and materialise at the edge. Only `_split_related` truly needs materialisation for slicing.

2) Type hints can reflect the iterator pipeline more clearly.
   - `_split_related` can accept `Iterable[str]` and materialise internally, allowing callers to stay lazy.

Recommendation
- Change `_normalise_lines`/`_filter_lines`/`_take_until_related_marker` to return `Iterator[str]`.
- Update `_split_related` to accept `Iterable[str]` and convert to tuple once.
