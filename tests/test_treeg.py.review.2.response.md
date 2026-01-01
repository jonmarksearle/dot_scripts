# Response — test_treeg.py.review.2

Agreements / changes applied
- Missing `_fail` tests + failure-first ordering are required once the invalid-input contract is defined.
- The deep-tree refactor and ids remain correct; no further changes needed there.
- Review/response files should be tracked; I will commit the review + response files to keep the repo clean.
- Change log placeholder/incomplete entry is real; I will append a corrective note rather than edit prior lines (append-only rule).

Pushback / constraints
- I will not rewrite historical `change_log.md` entries (append-only rule). Corrections will be appended as new notes.

Contract decision needed (to add `_fail` tests)
1) Forest is not iterable (e.g. `None`, `1`) — `TypeError`?
2) Forest contains non-`Node` (e.g. `"x"`, `None`) — `TypeError`?
3) `Node.children` contains non-`Node` — `TypeError`?
4) Non-`str` names — `TypeError`, or only drop empty-string and allow others?
