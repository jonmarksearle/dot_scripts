"""
clean_tree removes empty-name parents and drops their descendants.

Uses an explicit stack to avoid recursion depth limits on very deep trees.
Outputs newly constructed Nodes (no identity reuse).
Node validation happens at construction; clean_tree assumes valid Node inputs.
Validation runs on every Node construction and may add overhead on wide trees.
Runtime cost is linear in node count; no recursion depth limits.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Node:
    name: str
    children: tuple["Node", ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.name, str):
            raise TypeError("node name must be str")
        try:
            children = tuple(self.children)
        except TypeError as exc:
            raise TypeError("children must be iterable") from exc
        if any(not isinstance(child, Node) for child in children):
            raise TypeError("children must be Node")
        object.__setattr__(self, "children", children)

    @property
    def children_tuple(self) -> tuple["Node", ...]:
        return self.children


@dataclass(slots=True)
class Frame:
    """Mutable traversal frame; list avoids tuple churn on wide trees."""

    node: Node
    children: tuple[Node, ...]
    index: int = 0
    cleaned: list[Node] = field(default_factory=list)


class FrameStack:
    """
    Manages a stack of frames for post-order tree traversal.

    Encapsulates stack state and operations to keep traversal compact and
    explicit.
    """

    def __init__(self, root: Node) -> None:
        self._stack: list[Frame] = [Frame(root, root.children_tuple)]

    @property
    def is_empty(self) -> bool:
        """True if the stack has no frames."""
        return not self._stack

    @property
    def last_frame(self) -> Frame:
        """Top frame on the stack."""
        if self.is_empty:
            raise IndexError("Stack is empty")
        return self._stack[-1]

    @property
    def last_node(self) -> Node | None:
        """Cleaned node from the last frame, or None if dropped."""
        frame = self.last_frame
        if frame.node.name == "":
            return None
        return Node(frame.node.name, tuple(frame.cleaned))

    def push_child(self, child: Node) -> None:
        frame = self.last_frame
        frame.index += 1
        self._stack.append(Frame(child, child.children_tuple))

    def attach_child(self, child: Node | None) -> None:
        if child is None:
            return
        self.last_frame.cleaned.append(child)

    def pop_frame(self, built: Node | None) -> Node | None:
        self._stack.pop()
        if self.is_empty:
            return built
        self.attach_child(built)
        return None

    def step(self) -> Node | None:
        if self.is_empty:
            return None
        frame = self.last_frame
        if frame.index >= len(frame.children):
            built = self.last_node
            return self.pop_frame(built)
        self.push_child(frame.children[frame.index])
        return None


def _clean_node(root: Node) -> Node | None:
    stack = FrameStack(root)
    while not stack.is_empty:
        built = stack.step()
        if built is not None:
            return built
    return None


def _clean_tree(forest: Iterable[Node]) -> list[Node]:
    cleaned = (_clean_node(node) for node in iter(forest))
    return [node for node in cleaned if node is not None]


def clean_tree(forest: Iterable[Node]) -> list[Node]:
    """
    Clean a forest by removing empty-name parents and dropping their descendants.

    Input: iterable of root Nodes.
    Output: list of newly constructed Nodes (no identity reuse).
    Expects valid Node inputs; validation occurs at Node construction.
    """
    return _clean_tree(forest)
