"""
Tree cleaning and validation utilities.

This module provides `clean_tree`, a robust tool for filtering hierarchical data.
It removes nodes with empty names and—crucially—prunes their entire subtree.
It uses an explicit stack (heap memory) instead of recursion, so it won't crash
on trees deeper than the Mariana Trench (or Python's recursion limit).

Key features:
- **Iterative Traversal**: Safe for unlimited depth.
- **Strict Validation**: Nodes check their own types immediately.
- **Immutability**: Returns fresh Node instances; no side-effects on input.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Node:
    """
    An immutable tree node with strict type enforcement.

    Validation happens at the door: if you try to sneak in a non-string name
    or a child that isn't a Node, `__post_init__` will bounce you.
    """

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
        """A typed accessor for the children tuple."""
        return self.children


@dataclass(slots=True)
class Frame:
    """
    A mutable scratchpad for a single Node during traversal.

    Think of this as the "Work In Progress" tray for a parent node.
    It holds:
    - The `node` currently being processed.
    - Its `children` (cached as a tuple for speed).
    - An `index` pointer to the next child to visit.
    - A list of `cleaned` children (the good ones we're keeping).
    """

    node: Node
    children: tuple[Node, ...]
    index: int = 0
    cleaned: list[Node] = field(default_factory=list)


class FrameStack:
    """
    The engine room for iterative traversal.

    This class manages the stack of `Frame` objects. It replaces the call stack
    you'd use in recursion. It pushes children onto the stack to process them,
    and pops them off when they're done, handing the result back to the parent.
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
    Filters a forest of Nodes, removing any Node with an empty name string.

    If a Node is removed, its entire subtree is dropped with it (pruned).
    This function is safe for deeply nested structures that would blow the
    standard recursion limit.

    Args:
        forest: An iterable of root Nodes.

    Returns:
        A list of new, clean Node instances.
    """
    return _clean_tree(forest)
