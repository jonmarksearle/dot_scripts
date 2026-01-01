from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable


@dataclass(frozen=True, slots=True)
class Node:
    name: str
    children: tuple["Node", ...] = ()


def _iter_forest(forest: object) -> Iterable[Node]:
    try:
        return iter(forest)  # type: ignore[call-overload]
    except TypeError as exc:
        raise TypeError from exc


def build_tree_clean(forest: object) -> list[Node]:
    _iter_forest(forest)
    return []


def build_tree_dirty(forest: object) -> list[Node]:
    raise NotImplementedError
