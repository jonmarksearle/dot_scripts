# Response: `.scripts/treeg.py` review (n=5)

Thanks for the approval and notes.

## Acknowledged

- Terminology: will use “construction-validated model” (not “typed-only”) going forward.
- Validation overhead: accepted tradeoff and now documented.
- Test casts: kept as a justified exception to exercise runtime validation branches.

## Optional suggestion

- Not changing error message wording now to avoid churning the `match=` assertions, but open to revisiting if you want clearer UX.

