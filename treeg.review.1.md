# Review: `.scripts/treeg.py` (n=1)

Role: **Code Reviewer** (strict)

Scope: `.scripts/treeg.py` only. Tests referenced: `.scripts/tests/test_treeg.py`.

Requested focus: **convert `Frame` into a dataclass** while keeping behaviour consistent with tests and the module docstring.

Verdict: **Request changes**.

## Behavioural contract (as currently claimed / tested)

From the module docstring (`.scripts/treeg.py:1`):
- Removes empty-name parents and drops their descendants.
- Uses an explicit stack (no recursion depth limit).
- Outputs **newly constructed** `Node`s (no identity reuse).
- Raises `TypeError` for:
  - non-iterable forests,
  - non-`Node` elements,
  - invalid `Node` shapes (non-`str` names or non-iterable children).

From tests (`.scripts/tests/test_treeg.py`):
- Extremely broad success coverage via `CASES` + deep/wide trees.
- Negative tests assert `TypeError` for non-iterable forest, non-`Node` values, invalid children, and non-`str` names.
- Identity is not reused.

Any refactor (including “Frame as dataclass”) must preserve this behaviour, or you must update the docstring + tests together (not requested here).

## High severity issues (must fix)

### 1) `_ensure_node` is mis-typed and misleading

`_ensure_node` currently accepts `value: Node` (`.scripts/treeg.py:35`) but is used as a runtime guard over **arbitrary values** pulled from `children` (`.scripts/treeg.py:112`).

This is a correctness-of-types issue:
- It misleads the reader about the function’s purpose (it *does* validate “not Node” at runtime).
- It forces downstream type compromises (you’re already using `tuple[object, ...]` for children, which is right for lazy validation).

Required change:
- Make `_ensure_node` accept `object` (or `Node | object` if you insist, but `object` is the honest contract).

### 2) `Frame`’s type alias is internally inconsistent with `_children_tuple`

`_children_tuple` returns `tuple[object, ...]` (`.scripts/treeg.py:42`), but `Frame` claims the children tuple is `tuple[Node, ...]` (`.scripts/treeg.py:52`).

That mismatch is not cosmetic: it directly describes the key invariant of your algorithm (children are *raw/untrusted* until you `_ensure_node` them in traversal).

Required change:
- If you want **lazy** child validation (current behaviour), the frame must store `children: tuple[object, ...]`.
- If you want **eager** child validation (validate all children before traversal), then `_children_tuple` must return `tuple[Node, ...]` (by validating) *and* you must accept the behavioural change (you will now validate children even for subtrees that would be dropped; today you already traverse children, so the main change is when/how the `TypeError` is raised).

### 3) “Frame as dataclass” needs an explicit mutability decision

Your current `Frame` effectively contains mutable state:
- `index` increments.
- `cleaned` is mutated via `.append()` (`.scripts/treeg.py:96`).

Turning this into a dataclass without clarifying mutability will create subtle “frozen but not really” traps (e.g., `frozen=True` with a `list` field).

Required decision (pick one and be consistent):
1) **Mutable internal frame** (recommended for this algorithm):
   - `@dataclass(slots=True)` (not frozen)
   - fields: `node: Node`, `children: tuple[object, ...]`, `index: int`, `cleaned: list[Node]`
   - `cleaned.append(...)` stays (justify as a deliberate preference break: incremental build is clearer and avoids O(n²) tuple churn).
2) **Immutable frame** (not recommended unless you can prove clarity/perf):
   - `@dataclass(frozen=True, slots=True)` with `cleaned: tuple[Node, ...]`
   - every “append” becomes allocation of a new tuple
   - expect unnecessary churn on wide trees (you explicitly test wide roots at 3000 children).

If you choose (1), do *not* pretend it’s immutable. This is internal traversal state, not a domain/value object.

## Dataclass design recommendation (what “good” looks like here)

I would accept a change along these lines (names can vary):

- `@dataclass(slots=True)`
- `class Frame:`
  - `node: Node`
  - `children: tuple[object, ...]`  (raw; validated on access)
  - `index: int = 0`
  - `cleaned: list[Node] = field(default_factory=list)`

Then update `FrameStack` to store `list[Frame]` and to mutate `self._stack[-1].index += 1` etc.

Key invariants to preserve (make them obvious in code):
- `children` may contain non-`Node` values; only `_ensure_node(...)` produces a `Node`.
- `cleaned` contains **only validated** `Node` instances (or is empty).

## Strict style/standards feedback (should fix unless you can justify)

### 1) `.append()` usage must be justified (or redesigned)

Standards are clear: “avoid `.append()` in new code” (`CODE_STANDARDS.md` / `Standards/CODE_STANDARDS.new.md`).

However, this is one of the rare cases where `.append()` is likely the clearest and most efficient approach:
- you are incrementally building an ordered child list,
- and you test a very wide tree, where tuple concatenation would be pathological.

Required change:
- Either add a short comment/docstring note in `Frame` / `FrameStack` explaining why a mutable list is intentionally used (prevents the next reviewer from “fixing” it into O(n²)).
- Or redesign to avoid `.append()` without harming clarity/performance (I do not currently see a better option here).

### 2) Error messages are not asserted; choose consistency anyway

Your tests only assert `TypeError` (no `match=`), so message content is currently free to drift. That’s fine, but then:
- pick one clear, consistent style (“forest must be iterable”, “expected Node”, “node name must be str”, “children must be iterable”)
- keep it stable; it becomes part of the script’s UX.

### 3) Section dividers (`## ###############################################`) reduce signal

The “banner” comments split a small file into visually loud chunks (`.scripts/treeg.py:50`, `.scripts/treeg.py:126`).

Recommendation:
- Prefer normal whitespace + small, named helpers. If you keep separators, use a single `# ---` style line, once.

## Questions / clarifications for the author (answer in response doc)

1) Do you want to validate and potentially raise `TypeError` for invalid children even when the parent node will be dropped (empty name)?
   - Current traversal still visits children, so *yes*, invalid shapes in descendants should currently raise.
   - If you intend to short-circuit and skip validation for dropped subtrees, you must update the docstring and add tests.

2) Is `clean_tree`’s return type contract intentionally `list[Node]` (not `tuple[Node, ...]`)?
   - If yes, keep and document “list because callers expect list”.
   - If no, prefer `tuple` for immutability; but that will require adjusting tests.

## Next steps (expected from the author)

1) Convert `Frame` to a dataclass (with explicit mutability choice).
2) Fix `_ensure_node`’s signature to accept `object`.
3) Make frame children typing consistent with lazy validation (`tuple[object, ...]`), unless you intentionally switch to eager validation.
4) Run `.scripts` quality gate (at least `just test`) and keep behaviour identical to `.scripts/tests/test_treeg.py`.

Author response should go in `.scripts/treeg.review.1.response.md`.
