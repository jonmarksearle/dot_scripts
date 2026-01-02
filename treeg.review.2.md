# Review: `.scripts/treeg.py` (n=2)

Role: **Code Reviewer** (strict)

Scope: `.scripts/treeg.py` as currently implemented (Frame dataclass + eager child validation).

Question to answer: **Can we move some `Node | None` type hints to just `Node`?** Yes — and you should, because several current `Node | None` hints are incorrect/misleading given the runtime behaviour.

Verdict: **Request changes**.

## Summary (what improved)

- `Frame` is now a real, named type (`@dataclass(slots=True)`), which is clearer than a 4-tuple frame.
- Eager child validation in `_children_tuple()` is coherent with your intent (“defensive runtime guards”) and keeps traversal logic simple.

## High severity issues (must fix)

### 1) `Node | None` is used where `None` is impossible by construction

You now eagerly validate children in `_children_tuple()`:

- `_children_tuple()` returns `tuple(_valid_node(child) for child in children)` (`.scripts/treeg.py:42-49`).
- `_valid_node(...)` returns a `Node` or raises (`.scripts/treeg.py:35-40`).

Therefore, the result of `_children_tuple()` is **always** `tuple[Node, ...]` if it returns at all.

But you currently type it as `tuple[Node | None, ...]` (`.scripts/treeg.py:42`), and you propagate that into:
- `Frame.children: tuple[Node | None, ...]` (`.scripts/treeg.py:59`)
- extra runtime validation at every step: `child = _valid_node(frame.children[frame.index])` (`.scripts/treeg.py:120`)

This is a typing bug + clarity bug:
- the type claims `None` can appear in `children`, but the function guarantees it cannot.
- you are re-validating already-validated values due to your own incorrect type hints.

Required change:
- `_children_tuple(...) -> tuple[Node, ...]`
- `Frame.children: tuple[Node, ...]`
- In `step()`, take `child = frame.children[frame.index]` (no second validation).

This directly answers your question: **yes, you can and should replace `Node | None` with `Node` for `children`.**

### 2) “_ensure_node typing change” is still not honest about inputs

You renamed `_ensure_node` → `_valid_node`, but the signature is still not truthful:

`def _valid_node(value: Node | None) -> Node:` (`.scripts/treeg.py:35`)

In reality, this function is the runtime guard for “possibly not a Node” values coming from:
- forests (`_iter_nodes`),
- children tuples built from `node.children` that may be maliciously typed/cast (tests do this).

So the input is not “`Node | None`”; it is “unknown”.

Required change:
- `def _valid_node(value: object) -> Node:`

This makes your intent explicit and removes the need to sprinkle casts elsewhere.

### 3) FrameStack docstring quality regressed (clarity / correctness)

This is minor vs the typing bugs, but still should be fixed under your own standards:
- Spelling: “intterative” (`.scripts/treeg.py:69`)
- Double spaces and wordiness; the docstring repeats obvious information and is less precise than your previous version.

Required change:
- Fix spelling and tighten the docstring to “what invariant does this class enforce” rather than re-explaining recursion.

## Where `Node | None` is justified (keep it)

The optional return is a real part of the algorithm: empty-name nodes are dropped.

Places where `Node | None` is correct:
- `FrameStack.last_node: Node | None` (`.scripts/treeg.py:88-95`) because the top frame may be dropped.
- `attach_child(child: Node | None)` / `pop_frame(built: Node | None)` / `step() -> Node | None` because you thread “dropped” up the stack.
- `_clean_node(...) -> Node | None` because a root may be dropped.

If you want to eliminate `Node | None` *there*, you must redesign the control flow (e.g., use a dedicated sentinel object, or make `step()` always return a `Node` and represent “dropped” by not building frames for dropped nodes). That is a larger refactor and not warranted unless it clearly improves readability.

## Optional design feedback (non-blocking)

- The “section divider” banners are still noisy (`.scripts/treeg.py:51`, `.scripts/treeg.py:134`). I won’t block on it since you explicitly chose to keep them, but I still recommend replacing with normal spacing once the refactor settles.

## Acceptance criteria for this review (what I expect next)

1) Remove incorrect `Node | None` types from child storage:
   - `_children_tuple -> tuple[Node, ...]`
   - `Frame.children: tuple[Node, ...]`
   - `step()` uses the already-validated child directly
2) Change `_valid_node` to accept `object`.
3) Fix the FrameStack docstring typo and tighten wording.
4) Keep tests passing (`just format && just lint && just test` in `.scripts`).
