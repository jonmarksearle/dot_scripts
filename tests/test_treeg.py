from __future__ import annotations

import pytest

from tree_filter import Node, build_tree_clean, build_tree_dirty


def n(name: str, *children: Node) -> Node:
    return Node(name, tuple(children))


def chain(depth: int, name: str = "x") -> Node:
    node = Node(name)
    for _ in range(depth):
        node = Node(name, (node,))
    return node


def assert_chain(root: Node, depth: int, name: str = "x") -> None:
    node = root
    for _ in range(depth):
        assert node.name == name
        assert len(node.children) == 1
        node = node.children[0]
    assert node.name == name
    assert node.children == ()


CASES: list[tuple[tuple[Node, ...], list[Node]]] = [
    # 1-5: singletons
    ((n(""),), []),
    ((n("a"),), [n("a")]),
    ((n(" "),), [n(" ")]),
    ((n("0"),), [n("0")]),
    ((n("a",),), [n("a")]),
    # 6-10: small forests
    ((n(""), n("a")), [n("a")]),
    ((n("a"), n("")), [n("a")]),
    ((n("a"), n("b")), [n("a"), n("b")]),
    ((n(""), n("")), []),
    ((n("a"), n(""), n("b")), [n("a"), n("b")]),
    # 11-15: one-level children
    ((n("a", n("")),), [n("a")]),
    ((n("a", n("b")),), [n("a", n("b"))]),
    ((n("a", n(""), n("b")),), [n("a", n("b"))]),
    ((n("a", n("b"), n("")),), [n("a", n("b"))]),
    ((n("", n("b")),), []),
    # 16-20: two-level nesting
    ((n("a", n("b", n(""))),), [n("a", n("b"))]),
    ((n("a", n("b", n("c"))),), [n("a", n("b", n("c")))]),
    ((n("a", n("", n("c"))),), [n("a")]),
    ((n("a", n("b", n(""), n("c"))),), [n("a", n("b", n("c")))]),
    ((n("a", n(""), n("b", n(""))),), [n("a", n("b"))]),
    # 21-25: siblings and mixed depths
    ((n("a", n("b"), n("c")),), [n("a", n("b"), n("c"))]),
    ((n("a", n(""), n("c", n(""))),), [n("a", n("c"))]),
    ((n("a", n("b", n("c"), n("")), n("")),), [n("a", n("b", n("c")))]),
    ((n("a"), n("b", n("")), n(""), n("c")), [n("a"), n("b"), n("c")]),
    (
        (n("a", n("b")), n("", n("x")), n("c", n(""), n("d"))),
        [n("a", n("b")), n("c", n("d"))],
    ),
    # 26-30: deeper mixed structures
    ((n("a", n("b", n("c", n("")))),), [n("a", n("b", n("c")))]),
    ((n("a", n("b", n("", n("d"))), n("c")),), [n("a", n("b"), n("c"))]),
    ((n("a", n("b", n("c", n("d"))), n("")),), [n("a", n("b", n("c", n("d"))))]),
    (
        (n("a", n(""), n("b", n("c", n(""))), n("d")),),
        [n("a", n("b", n("c")), n("d"))],
    ),
    (
        (n("a", n("b", n(""), n("c", n(""), n("d")))),),
        [n("a", n("b", n("c", n("d"))))],
    ),
    # 31-35: multiple roots with nested filtering
    ((n(""), n("a", n("b")), n("c", n(""))), [n("a", n("b")), n("c")]),
    (
        (n("a", n(""), n("b")), n(""), n("c", n("d", n("")))),
        [n("a", n("b")), n("c", n("d"))],
    ),
    (
        (n("a", n("b", n("c"), n(""))), n("d", n(""), n("e"))),
        [n("a", n("b", n("c"))), n("d", n("e"))],
    ),
    ((n("a", n("b", n("", n("x")))), n("c")), [n("a", n("b")), n("c")]),
    (
        (n("a", n("", n("x"))), n("b", n("c", n(""), n("d")))),
        [n("a"), n("b", n("c", n("d")))],
    ),
    # 36-40: gnarlier nesting
    (
        (n("a", n("b", n("c", n(""), n("d"))), n("")),),
        [n("a", n("b", n("c", n("d"))))],
    ),
    (
        (n("a", n("b", n(""), n("c", n("d", n(""))))),),
        [n("a", n("b", n("c", n("d"))))],
    ),
    (
        (n("a", n(""), n("b", n("c", n(""), n("d", n("")))), n("e")),),
        [n("a", n("b", n("c", n("d"))), n("e"))],
    ),
    (
        (n("a", n("b", n("c", n("d", n("e", n("")))))),),
        [n("a", n("b", n("c", n("d", n("e")))))],
    ),
    (
        (n("a", n("b", n("c"), n(""), n("d", n(""), n("e")))),),
        [n("a", n("b", n("c"), n("d", n("e"))))],
    ),
    # 41-45: wide trees
    (
        (n("a", n(""), n("b"), n(""), n("c"), n(""), n("d")),),
        [n("a", n("b"), n("c"), n("d"))],
    ),
    (
        (n("a", n("b"), n(""), n("c"), n("d", n(""), n("e")), n(""), n("f")),),
        [n("a", n("b"), n("c"), n("d", n("e")), n("f"))],
    ),
    (
        (n("a", n("b", n(""), n("c")), n(""), n("d", n("e"), n(""), n("f"))),),
        [n("a", n("b", n("c")), n("d", n("e"), n("f")))],
    ),
    (
        (n("a", n(""), n("b", n(""), n("c"), n("d", n(""))), n("e")),),
        [n("a", n("b", n("c"), n("d")), n("e"))],
    ),
    (
        (n("a", n("b"), n("c"), n("d"), n("e"), n("f"), n("")),),
        [n("a", n("b"), n("c"), n("d"), n("e"), n("f"))],
    ),
    # 46-49: very nested, mixed
    (
        (n("a", n("b", n("c", n(""), n("d", n(""), n("e"))))),),
        [n("a", n("b", n("c", n("d", n("e")))))],
    ),
    (
        (
            n(
                "a",
                n(
                    "b",
                    n(""),
                    n("c", n("d", n(""), n("e", n(""))), n("f")),
                ),
            ),
        ),
        [n("a", n("b", n("c", n("d", n("e")), n("f"))))],
    ),
    (
        (
            n(
                "a",
                n(""),
                n("b", n("c", n("d", n(""), n("e"))), n(""), n("f")),
                n("g", n("")),
            ),
            n("h", n("")),
        ),
        [
            n("a", n("b", n("c", n("d", n("e"))), n("f")), n("g")),
            n("h"),
        ],
    ),
    (
        (n("a", n("b", n("c", n("d", n(""), n("e", n("f", n(""))))))),),
        [n("a", n("b", n("c", n("d", n("e", n("f"))))))],
    ),
    # 50: forest with mixed wide+deep
    (
        (
            n(""),
            n(
                "root",
                n(""),
                n("a", n(""), n("b", n(""), n("c"))),
                n("d", n("e", n(""), n("f")), n("")),
                n(""),
                n("g"),
            ),
            n("tail", n("", n("x")), n("y")),
            n(""),
        ),
        [
            n("root", n("a", n("b", n("c"))), n("d", n("e", n("f"))), n("g")),
            n("tail", n("y")),
        ],
    ),
]

CASE_IDS: list[str] = [
    "singleton-empty",
    "singleton-a",
    "singleton-space",
    "singleton-zero",
    "singleton-a-explicit",
    "forest-empty-a",
    "forest-a-empty",
    "forest-a-b",
    "forest-empty-empty",
    "forest-a-empty-b",
    "child-empty",
    "child-b",
    "children-empty-b",
    "children-b-empty",
    "root-empty-child-b",
    "two-level-empty-grandchild",
    "two-level-abc",
    "two-level-empty-child-with-c",
    "two-level-b-empty-c",
    "two-level-empty-and-b-empty",
    "siblings-b-c",
    "siblings-empty-and-c-empty",
    "siblings-bc-empty-tail",
    "forest-mixed-empty",
    "forest-mixed-nested",
    "deep-abc-empty",
    "deep-b-empty-d-c",
    "deep-abcd-empty-tail",
    "deep-mixed-bc-empty",
    "deep-b-empty-c-empty-d",
    "roots-empty-a-b-c-empty",
    "roots-a-empty-b-cd-empty",
    "roots-abc-empty-de-empty",
    "roots-ax-c",
    "roots-a-empty-bcd-empty",
    "gnarly-b-c-empty-d",
    "gnarly-b-empty-cd-empty",
    "gnarly-a-empty-bcd-empty-e",
    "gnarly-abcde-empty",
    "gnarly-bc-empty-d-empty-e",
    "wide-a-b-c-d",
    "wide-b-c-de-empty-f",
    "wide-b-empty-c-d-e-empty-f",
    "wide-a-empty-b-empty-cd-empty-e",
    "wide-a-b-c-d-e-f-empty",
    "mixed-c-empty-d-empty-e",
    "mixed-b-empty-cde-f",
    "mixed-forest-a-h",
    "mixed-deep-f",
    "forest-root-tail",
]

FORESTS_NOT_ITERABLE: tuple[object, ...] = (None, 1)
FORESTS_WITH_NON_NODE: tuple[tuple[object, ...], ...] = (("x",), (None,))
FORESTS_WITH_INVALID_CHILDREN: tuple[tuple[Node, ...], ...] = (
    (Node("a", ("x",)),),
    (Node("a", (None,)),),
)
FORESTS_WITH_NON_STR_NAME: tuple[tuple[Node, ...], ...] = (
    (Node(1, ()),),
    (Node(None, ()),),
)


@pytest.mark.parametrize("forest", FORESTS_NOT_ITERABLE, ids=["none", "int"])
def test__build_tree_clean__forest_not_iterable__fail(forest: object) -> None:
    with pytest.raises(TypeError):
        build_tree_clean(forest)


@pytest.mark.parametrize("forest", FORESTS_NOT_ITERABLE, ids=["none", "int"])
def test__build_tree_dirty__forest_not_iterable__fail(forest: object) -> None:
    with pytest.raises(TypeError):
        build_tree_dirty(forest)


@pytest.mark.parametrize("forest", FORESTS_WITH_NON_NODE, ids=["str", "none"])
def test__build_tree_clean__forest_contains_non_node__fail(forest: tuple[object, ...]) -> None:
    with pytest.raises(TypeError):
        build_tree_clean(forest)


@pytest.mark.parametrize("forest", FORESTS_WITH_NON_NODE, ids=["str", "none"])
def test__build_tree_dirty__forest_contains_non_node__fail(forest: tuple[object, ...]) -> None:
    with pytest.raises(TypeError):
        build_tree_dirty(forest)


@pytest.mark.parametrize("forest", FORESTS_WITH_INVALID_CHILDREN, ids=["child-str", "child-none"])
def test__build_tree_clean__children_contains_non_node__fail(forest: tuple[Node, ...]) -> None:
    with pytest.raises(TypeError):
        build_tree_clean(forest)


@pytest.mark.parametrize("forest", FORESTS_WITH_INVALID_CHILDREN, ids=["child-str", "child-none"])
def test__build_tree_dirty__children_contains_non_node__fail(forest: tuple[Node, ...]) -> None:
    with pytest.raises(TypeError):
        build_tree_dirty(forest)


@pytest.mark.parametrize("forest", FORESTS_WITH_NON_STR_NAME, ids=["name-int", "name-none"])
def test__build_tree_clean__name_not_str__fail(forest: tuple[Node, ...]) -> None:
    with pytest.raises(TypeError):
        build_tree_clean(forest)


@pytest.mark.parametrize("forest", FORESTS_WITH_NON_STR_NAME, ids=["name-int", "name-none"])
def test__build_tree_dirty__name_not_str__fail(forest: tuple[Node, ...]) -> None:
    with pytest.raises(TypeError):
        build_tree_dirty(forest)


@pytest.mark.parametrize("forest,expected", CASES, ids=CASE_IDS)
def test__build_tree_clean__cases__success(forest: tuple[Node, ...], expected: list[Node]) -> None:
    assert build_tree_clean(forest) == expected


@pytest.mark.parametrize("forest,expected", CASES, ids=CASE_IDS)
def test__build_tree_dirty__cases__success(forest: tuple[Node, ...], expected: list[Node]) -> None:
    assert build_tree_dirty(forest) == expected


def test__build_tree_clean__accepts_generator__success() -> None:
    forest = (n("a", n(""), n("b")), n(""))
    gen = (x for x in forest)
    assert build_tree_clean(gen) == [n("a", n("b"))]


def test__build_tree_dirty__accepts_generator__success() -> None:
    forest = (n("a", n(""), n("b")), n(""))
    gen = (x for x in forest)
    assert build_tree_dirty(gen) == [n("a", n("b"))]


def test__build_tree_clean__returns_copy_not_same_objects__success() -> None:
    child = n("c")
    root = n("a", child)
    out = build_tree_clean([root])
    assert out[0] is not root
    assert out[0].children[0] is not child


def test__build_tree_dirty__returns_copy_not_same_objects__success() -> None:
    child = n("c")
    root = n("a", child)
    out = build_tree_dirty([root])
    assert out[0] is not root
    assert out[0].children[0] is not child


def test__build_tree_clean__supports_very_deep_tree__success() -> None:
    root = chain(5000)
    out = build_tree_clean([root])
    assert len(out) == 1
    assert_chain(out[0], 5000)


def test__build_tree_dirty__supports_very_deep_tree__success() -> None:
    root = chain(5000)
    out = build_tree_dirty([root])
    assert len(out) == 1
    assert_chain(out[0], 5000)


def test__build_tree_clean__excluded_parent_drops_subtree__success() -> None:
    assert build_tree_clean([n("", n("ok"))]) == []


def test__build_tree_dirty__excluded_parent_drops_subtree__success() -> None:
    assert build_tree_dirty([n("", n("ok"))]) == []
