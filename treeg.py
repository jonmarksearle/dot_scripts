"""
clean_tree removes empty-name parents and drops their descendants.

Uses an explicit stack to avoid recursion depth limits on very deep trees.
Outputs newly constructed Nodes (no identity reuse).
Raises TypeError for non-iterable forests, non-Node elements, and invalid Node
shapes (non-str names or non-iterable children).
Runtime cost is linear in node count; no recursion depth limits.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass


type Frame = tuple["Node", tuple[object, ...], int, list["Node"]]


@dataclass(frozen=True, slots=True)
class Node:
    name: str
    children: tuple["Node", ...] = ()


def _iter_forest(forest: object) -> Iterator[object]:
    """Defensive guard for non-iterable forests with a consistent TypeError."""
    if not isinstance(forest, Iterable):
        raise TypeError("forest must be iterable")
    return iter(forest)


def _validate_name(node: Node) -> None:
    if not isinstance(node.name, str):
        raise TypeError("node name must be str")


def _ensure_node(value: object) -> Node:
    if not isinstance(value, Node):
        raise TypeError("expected Node")
    _validate_name(value)
    return value


def _children_tuple(node: Node) -> tuple[object, ...]:
    """Normalise children to a tuple, raising for non-iterable shapes."""
    try:
        return tuple(node.children)
    except TypeError as exc:
        raise TypeError("children must be iterable") from exc


## ###############################################


class FrameStack:
    """
    Manages a stack of frames for post-order tree traversal.

    Encapsulates stack state and operations to reduce argument threading and
    enforce invariants (e.g., no operations on empty stack). Methods are minimal
    primitives for building up traversal logic.
    """

    def __init__(self, root: Node) -> None:
        self._stack: list[Frame] = [(root, _children_tuple(root), 0, [])]

    @property
    def last_frame(self) -> Frame:
        """Top frame on the stack."""
        if not self._stack:
            raise IndexError("Stack is empty")
        return self._stack[-1]

    @property
    def is_empty(self) -> bool:
        """True if the stack has no frames."""
        return not self._stack

    @property
    def last_node(self) -> Node | None:
        """Cleaned node from the last frame, or None if dropped."""
        node, _children, _index, cleaned = self.last_frame
        if node.name == "":
            return None
        return Node(node.name, tuple(cleaned))

    def push_child(self, child: Node) -> None:
        node, children, index, cleaned = self.last_frame
        self._stack[-1] = (node, children, index + 1, cleaned)
        self._stack.append((child, _children_tuple(child), 0, []))

    def attach_child(self, child: Node | None) -> None:
        if child is None:
            return
        _node, _children, _index, cleaned = self.last_frame
        cleaned.append(child)

    def pop_frame(self, built: Node | None) -> Node | None:
        self._stack.pop()
        if self.is_empty:
            return built
        self.attach_child(built)
        return None

    def step(self) -> Node | None:
        if self.is_empty:
            return None
        node, children, index, _cleaned = self.last_frame
        if index >= len(children):
            built = self.last_node
            return self.pop_frame(built)
        child = _ensure_node(children[index])
        self.push_child(child)
        return None


def _clean_node(root: Node) -> Node | None:
    stack = FrameStack(root)
    while not stack.is_empty:
        built = stack.step()
        if built is not None:
            return built
    return None


## ###############################################


def _iter_nodes(forest: Iterable[Node]) -> Iterator[Node]:
    return (_ensure_node(node) for node in _iter_forest(forest))


def _clean_tree(forest: Iterable[Node]) -> list[Node]:
    cleaned = (_clean_node(node) for node in _iter_nodes(forest))
    return [node for node in cleaned if node is not None]


def clean_tree(forest: Iterable[Node]) -> list[Node]:
    """
    Clean a forest by removing empty-name parents and dropping their descendants.

    Input: iterable of root Nodes.
    Output: list of newly constructed Nodes (no identity reuse).
    Raises TypeError for non-iterable forests, non-Node elements, and invalid
    Node shapes (non-str names or non-iterable children).
    """
    return _clean_tree(forest)
