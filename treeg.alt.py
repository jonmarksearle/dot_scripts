"""treeg.py – simple utilities for pruning and validating trees."""

from __future__ import annotations

import sys
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Tuple

# Ensure deep recursion (≥ 5 000) doesn’t blow up.
sys.setrecursionlimit(max(sys.getrecursionlimit(), 10_000))


@dataclass(frozen=True, slots=True)
class Node:
    """Immutable tree node."""

    name: str
    children: Tuple["Node", ...] = ()


def clean_tree(forest: Iterable[Node]) -> list[Node]:
    """
    Return a copy of *forest* with every subtree whose root ``name`` is
    the empty string excluded.

    The function also *validates* the entire structure:

    * *forest* must be iterable.
    * Every element must be a :class:`Node`.
    * ``Node.name`` must be ``str``.
    * ``Node.children`` must be a tuple of :class:`Node` objects.

    Violations raise :class:`TypeError`.
    """
    if not isinstance(forest, Iterable):
        raise TypeError("forest must be an iterable of Node objects")

    def _clean(node: object) -> Node | None:
        if not isinstance(node, Node):
            raise TypeError("forest must contain only Node objects")
        if not isinstance(node.name, str):
            raise TypeError("Node.name must be str")
        if not isinstance(node.children, tuple):
            raise TypeError("Node.children must be a tuple")

        # Process children first so we can attach the cleaned copies.
        kept_children: list[Node] = []
        for child in node.children:
            if not isinstance(child, Node):
                raise TypeError("Node.children must contain only Node objects")
            cleaned = _clean(child)
            if cleaned is not None:
                kept_children.append(cleaned)

        # Drop the current node (and hence its cleaned children) if name is "".
        return None if node.name == "" else Node(node.name, tuple(kept_children))

    cleaned: list[Node] = []
    for root in forest:
        pruned = _clean(root)
        if pruned is not None:
            cleaned.append(pruned)
    return cleaned

