"""
clean_tree removes empty-name parents and drops their descendants.

Uses an explicit stack to avoid recursion depth limits on very deep trees.
Outputs newly constructed Nodes (no identity reuse).
build_tree remains as a deprecated alias for one cycle and will be removed.
Raises TypeError for non-iterable forests, non-Node elements, and invalid Node
shapes (non-str names or non-iterable children).
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass


type Frame = tuple["Node", tuple[object, ...], int, tuple["Node", ...]]


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
    try:
        return tuple(node.children)
    except TypeError as exc:
        raise TypeError("children must be iterable") from exc


def _iter_nodes(forest: Iterable[Node]) -> Iterator[Node]:
    return (_ensure_node(node) for node in _iter_forest(forest))


def _attach_child(stack: tuple[Frame, ...], child: Node | None) -> tuple[Frame, ...]:
    if child is None:
        return stack
    node, children, index, cleaned = stack[-1]
    return (*stack[:-1], (node, children, index, (*cleaned, child)))


def _push_child(stack: tuple[Frame, ...], child: Node) -> tuple[Frame, ...]:
    node, children, index, cleaned = stack[-1]
    updated_parent = (node, children, index + 1, cleaned)
    frame = (child, _children_tuple(child), 0, ())
    return (*stack[:-1], updated_parent, frame)


def _initial_stack(root: Node) -> tuple[Frame, ...]:
    """
    Seed the stack with a single frame.

    Frame fields: (node, children, index, cleaned)
    - node: current node being processed
    - children: original child sequence (as a tuple)
    - index: next child index to process
    - cleaned: already-cleaned child nodes in order
    """
    return ((root, _children_tuple(root), 0, ()),)


def _finalise_frame(frame: Frame) -> Node | None:
    """
    Build the cleaned node for a completed frame.

    Returns None when the node name is empty (drop subtree); otherwise returns a
    new Node with cleaned children.
    """
    node, _children, _index, cleaned = frame
    if node.name == "":
        return None
    return Node(node.name, cleaned)


def _pop_frame(
    stack: tuple[Frame, ...], built: Node | None
) -> tuple[tuple[Frame, ...], Node | None]:
    """
    Pop a completed frame and attach its built node to the parent.

    Returns (new_stack, built) where built is only returned when the popped
    frame was the root.
    """
    remainder = stack[:-1]
    if not remainder:
        return (), built
    return (_attach_child(remainder, built), None)


def _step_stack(stack: tuple[Frame, ...]) -> tuple[tuple[Frame, ...], Node | None]:
    """
    Advance the traversal by one step.

    Either pushes the next child frame or finalises the current frame. Returns
    (new_stack, built) where built is only non-None when the root is finalised.
    """
    node, children, index, _cleaned = stack[-1]
    if index >= len(children):
        built = _finalise_frame(stack[-1])
        return _pop_frame(stack, built)
    child = _ensure_node(children[index])
    return (_push_child(stack, child), None)


def _clean_node(root: Node) -> Node | None:
    stack = _initial_stack(root)
    while stack:
        stack, built = _step_stack(stack)
        if built is not None or not stack:
            return built
    return None


def _clean_tree(forest: Iterable[Node]) -> list[Node]:
    cleaned = (_clean_node(node) for node in _iter_nodes(forest))
    return [node for node in cleaned if node is not None]


def clean_tree(forest: Iterable[Node]) -> list[Node]:
    """
    Clean nodes by removing empty-name parents and dropping their descendants.

    The returned nodes are newly constructed (no object identity reuse).
    """
    return _clean_tree(forest)
