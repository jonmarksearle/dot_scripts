from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass


type Frame = tuple["Node", tuple[object, ...], int, tuple["Node", ...]]


@dataclass(frozen=True, slots=True)
class Node:
    name: str
    children: tuple["Node", ...] = ()


def _iter_forest(forest: object) -> Iterator[object]:
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


def _iter_nodes(forest: object) -> Iterator[Node]:
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
    return ((root, _children_tuple(root), 0, ()),)


def _finalise_frame(frame: Frame) -> Node | None:
    node, _children, _index, cleaned = frame
    if node.name == "":
        return None
    return Node(node.name, cleaned)


def _pop_frame(
    stack: tuple[Frame, ...], built: Node | None
) -> tuple[tuple[Frame, ...], Node | None]:
    remainder = stack[:-1]
    if not remainder:
        return (), built
    return (_attach_child(remainder, built), None)


def _step_stack(stack: tuple[Frame, ...]) -> tuple[tuple[Frame, ...], Node | None]:
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


def _build_tree(forest: object) -> list[Node]:
    cleaned = (_clean_node(node) for node in _iter_nodes(forest))
    return [node for node in cleaned if node is not None]


def build_tree_clean(forest: object) -> list[Node]:
    """Return a new tree list with empty-name nodes removed."""
    return _build_tree(forest)


def build_tree_dirty(forest: object) -> list[Node]:
    """Return a new tree list with empty-name nodes removed."""
    return _build_tree(forest)
