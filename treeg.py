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
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Node:
    name: str
    children: tuple["Node", ...] = ()


def _iter_forest(forest: Iterable[Node]) -> Iterator[Node]:
    """Defensive guard for non-iterable forests with a consistent TypeError."""
    if not isinstance(forest, Iterable):
        raise TypeError("forest must be iterable")
    return iter(forest)


def _validate_name(node: Node) -> None:
    if not isinstance(node.name, str):
        raise TypeError("node name must be str")


def _valid_node(value: object) -> Node:
    if not isinstance(value, Node):
        raise TypeError("expected Node")
    _validate_name(value)
    return value


def _children_tuple(node: Node) -> tuple[Node, ...]:
    """Normalise children to a tuple, raising for non-iterable shapes."""
    try:
        children = tuple(node.children)
    except TypeError as exc:
        raise TypeError("children must be iterable") from exc
    return tuple(_valid_node(child) for child in children)


## ###############################################


@dataclass(slots=True)
class Frame:
    """Mutable traversal frame; cleaned list is built up incrementally."""

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
        self._stack: list[Frame] = [Frame(root, _children_tuple(root))]

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
        self._stack.append(Frame(child, _children_tuple(child)))

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


## ###############################################


def _iter_nodes(forest: Iterable[Node]) -> Iterator[Node]:
    return (_valid_node(node) for node in _iter_forest(forest))


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
