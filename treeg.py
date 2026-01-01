from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


type Frame = tuple["Node", tuple["Node", ...], int, tuple["Node", ...]]


@dataclass(frozen=True, slots=True)
class Node:
    name: str
    children: tuple["Node", ...] = ()


def _iter_forest(forest: object) -> Iterable[object]:
    try:
        return iter(forest)  # type: ignore[call-overload]
    except TypeError as exc:
        raise TypeError from exc


def _validate_name(node: Node) -> None:
    if not isinstance(node.name, str):
        raise TypeError


def _ensure_node(value: object) -> Node:
    if not isinstance(value, Node):
        raise TypeError
    _validate_name(value)
    return value


def _children_tuple(node: Node) -> tuple[Node, ...]:
    try:
        return tuple(node.children)
    except TypeError as exc:
        raise TypeError from exc


def _iter_nodes(forest: object) -> Iterable[Node]:
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


def _clean_node(root: Node) -> Node | None:
    _validate_name(root)
    stack: tuple[Frame, ...] = ((root, _children_tuple(root), 0, ()),)
    while stack:
        node, children, index, cleaned = stack[-1]
        if index >= len(children):
            built = None if node.name == "" else Node(node.name, cleaned)
            stack = stack[:-1]
            if not stack:
                return built
            stack = _attach_child(stack, built)
            continue
        child = _ensure_node(children[index])
        stack = _push_child(stack, child)
    return None


def _build_tree(forest: object) -> list[Node]:
    cleaned = (_clean_node(node) for node in _iter_nodes(forest))
    return [node for node in cleaned if node is not None]


def build_tree_clean(forest: object) -> list[Node]:
    return _build_tree(forest)


def build_tree_dirty(forest: object) -> list[Node]:
    return _build_tree(forest)
