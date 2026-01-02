from __future__ import annotations

from typing import cast

import pytest

from treeg import Node, clean_tree


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
    (
        (
            n(
                "a",
            ),
        ),
        [n("a")],
    ),
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

BAD_NAME_VALUES: tuple[object, ...] = (1, None)
BAD_CHILDREN_VALUES: tuple[object, ...] = (
    1,
    ("x",),
    (None,),
    ("x", Node("a")),
    (Node("a"), "x"),
)


@pytest.mark.parametrize("name", BAD_NAME_VALUES, ids=["int", "none"])
def test__Node__name_not_str__fail(name: object) -> None:
    with pytest.raises(TypeError):
        Node(cast(str, name))


@pytest.mark.parametrize(
    "children",
    BAD_CHILDREN_VALUES,
    ids=["int", "str", "none", "str-node", "node-str"],
)
def test__Node__children_invalid__fail(children: object) -> None:
    with pytest.raises(TypeError):
        Node("a", cast(tuple[Node, ...], children))


@pytest.mark.parametrize("forest,expected", CASES, ids=CASE_IDS)
def test__clean_tree__cases__success(
    forest: tuple[Node, ...], expected: list[Node]
) -> None:
    assert clean_tree(forest) == expected


def test__clean_tree__accepts_generator__success() -> None:
    forest = (n("a", n(""), n("b")), n(""))
    gen = (x for x in forest)
    assert clean_tree(gen) == [n("a", n("b"))]


def test__clean_tree__returns_copy_not_same_objects__success() -> None:
    child = n("c")
    root = n("a", child)
    out = clean_tree([root])
    assert out[0] is not root
    assert out[0].children[0] is not child


def test__clean_tree__supports_very_deep_tree__success() -> None:
    root = chain(5000)
    out = clean_tree([root])
    assert len(out) == 1
    assert_chain(out[0], 5000)


def test__clean_tree__excluded_parent_drops_subtree__success() -> None:
    assert clean_tree([n("", n("ok"))]) == []


def test__clean_tree__very_wide_root__success() -> None:
    root = n("root", *(n(f"c{i}") for i in range(3000)))
    out = clean_tree([root])
    assert out == [root]
