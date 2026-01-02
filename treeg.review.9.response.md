# Code Author Response: treeg.py (review 9)

Thanks for the review. I’ve addressed the treeg.py items and noted the treeg.alt.py point below.

## Accepted
1) **Module docstring correctness**: Agreed. I removed the stale `build_tree` alias claim from the module docstring.
2) **Quadratic stack copying**: Agreed. I switched the stack to a `list[Frame]` and update it in-place to avoid tuple-copy churn on deep chains.
3) **clean_tree contract docstring**: Agreed. I expanded the docstring to name the forest input, the pruning rule, fresh-node output, and high-level `TypeError` conditions.

## Noted (out of scope for this change)
- **treeg.alt.py import-time recursion limit**: Agreed this is a correctness/composability issue. I didn’t touch `treeg.alt.py` in this change because the task scope was to update `treeg.py`. Happy to tackle that in a follow-up if desired.

## Verification
- `just format`
- `just lint`
- `just test`

All gates are green.
