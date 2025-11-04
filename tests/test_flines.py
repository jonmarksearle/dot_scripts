from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from flines import _collect, _read, FunctionInfo


@pytest.fixture
def sample_python_file(tmp_path: Path) -> Path:
    content = dedent(
        """
        def func_a():
            pass

        class MyClass:
            def method_b(self):
                pass

            async def method_c(self):
                # Line 1
                # Line 2
                pass

        def func_d():
            # Line 1
            # Line 2
            # Line 3
            pass

        async def func_e():
            pass
        """
    )
    file_path = tmp_path / "sample.py"
    file_path.write_text(content)
    return file_path


def test__collect__basic_functions__success(sample_python_file: Path) -> None:
    tree = _read(sample_python_file)
    functions = _collect(tree)

    expected = [
        FunctionInfo(qualname="func_a", lineno=2, end_lineno=3),
        FunctionInfo(qualname="MyClass.method_b", lineno=6, end_lineno=7),
        FunctionInfo(qualname="MyClass.method_c", lineno=9, end_lineno=12),
        FunctionInfo(qualname="func_d", lineno=14, end_lineno=18),
        FunctionInfo(qualname="func_e", lineno=20, end_lineno=21),
    ]
    assert functions == expected


def test__collect__no_functions__success(tmp_path: Path) -> None:
    content = dedent(
        """
        # Just comments
        x = 10
        """
    )
    file_path = tmp_path / "empty.py"
    file_path.write_text(content)
    tree = _read(file_path)
    functions = _collect(tree)
    assert functions == []


def test__collect__function_line_counts__success(sample_python_file: Path) -> None:
    tree = _read(sample_python_file)
    functions = _collect(tree)

    func_c = next(f for f in functions if f.qualname == "MyClass.method_c")
    assert func_c.end_lineno - func_c.lineno + 1 == 4  # 9, 10, 11, 12

    func_d = next(f for f in functions if f.qualname == "func_d")
    assert func_d.end_lineno - func_d.lineno + 1 == 5  # 14, 15, 16, 17, 18


def test__collect__async_functions__success(sample_python_file: Path) -> None:
    tree = _read(sample_python_file)
    functions = _collect(tree)

    func_e = next(f for f in functions if f.qualname == "func_e")
    assert func_e.lineno == 20
    assert func_e.end_lineno == 21


def test__collect__nested_functions__success(tmp_path: Path) -> None:
    content = dedent(
        """
        def outer():
            def inner():
                pass
            pass
        """
    )
    file_path = tmp_path / "nested.py"
    file_path.write_text(content)
    tree = _read(file_path)
    functions = _collect(tree)

    expected = [
        FunctionInfo(qualname="outer", lineno=2, end_lineno=5),
        FunctionInfo(qualname="outer.inner", lineno=3, end_lineno=4),
    ]
    assert functions == expected
