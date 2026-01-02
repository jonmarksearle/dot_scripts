# Code Review: treeg.py (+ notes on treeg.alt.py) (review 9)

Role: Code Reviewer (strict)

Reference: `/home/jon/Work/.scripts/tree.review.8.md`.

Standards note: per `CODE_STANDARDS.new.md`, **principles trump preferences/avoidances**. I’m using that lens here: if a small, local mutation makes the code *more correct for real inputs* and *more obvious*, do it.

## Summary
`clean_tree` in `treeg.py` is functionally correct for the current tests, and the frame/stack docstrings are a genuine readability improvement.

However, the peer review correctly identifies two serious problems that need action:
1) `treeg.py` currently has a **performance foot-gun** (tuple-stack copying → quadratic behaviour on deep chains).
2) `treeg.alt.py` has an **import-time global side effect** (`sys.setrecursionlimit(...)`) which is unacceptable for reusable code.

Additionally, there is a **docstring correctness bug** in `treeg.py` right now.

## Action required (treeg.py)
1) **Fix the module docstring: it currently claims a deprecated `build_tree` alias exists, but no alias is defined.**
   - See `treeg.py:6` vs file content (no `build_tree` symbol).
   - This violates the top standard principle (correctness) and will mislead fresh readers.
   - Required: either reintroduce an actual alias with explicit deprecation semantics *or* delete that sentence.

2) **Fix quadratic stack behaviour (principles > “avoid mutation”).**
   - The peer review’s diagnosis is correct: these tuple operations copy the entire stack repeatedly:
     - `treeg.py:60` (`(*stack[:-1], ...)`)
     - `treeg.py:67` (`(*stack[:-1], updated_parent, frame)`)
   - On a long chain, this becomes O(d²) copying/allocation churn.
   - Even though “performance” is lower priority than clarity, this is not a micro-optimisation: the algorithm is explicitly positioned as “safe for very deep trees” (`treeg.py:4`), and deep chains are exactly where this design regresses.
   - Required: switch the stack representation from `tuple[Frame, ...]` to `list[Frame]` and update in place.
     - This is an allowed preference break: local, contained mutation improves real-world correctness (finishes fast), and typically makes the control flow *simpler*, not harder.

3) **Fresh-reader docstring pass for `clean_tree`.**
   - `treeg.py:140-146` is close, but I’d require it to explicitly name the input/output contract:
     - input is a forest (iterable of root `Node`s)
     - nodes with `name == ""` are removed and their descendants are dropped
     - output nodes are freshly constructed (no identity reuse)
     - `TypeError` conditions at a high level (no need to repeat every helper message)

## Action required (treeg.alt.py)
1) **Remove import-time `sys.setrecursionlimit(...)`.**
   - `treeg.alt.py:11` mutates a process-wide setting at import time.
   - This is a correctness/composability violation; it can change behaviour of unrelated code in the same process.
   - Required: either delete `treeg.alt.py` entirely, or make recursion-limit adjustment an explicit opt-in action (e.g., a `main()` or a dedicated function) and keep the library surface side-effect free.

2) **Do not treat `treeg.alt.py` as “production alternative” unless you also remove the depth hazard.**
   - If it remains recursive, it should either:
     - clearly document recursion depth limitations, or
     - not be presented as equivalent to the iterative implementation.

## Notes (agreement with peer review #8)
- The performance critique of `treeg.py` is valid.
- The import-time recursion-limit change in `treeg.alt.py` is a major flaw.

## Notes (principles vs preferences)
- If the best fix uses a mutable stack list and local mutation, that is an acceptable preference break.
- Similarly, use of `.append()` in tests or traversal code is acceptable when it is the clearest expression of the algorithm and remains local.
