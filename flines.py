#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "typer>=0.12",
#   "rich>=13.7",
# ]
# [tool.uv]
# # Optional for reproducibility of resolutions:
# # exclude-newer = "2025-11-01"
# ///
from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Iterator, Iterable

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(add_completion=False, no_args_is_help=True)
console = Console()


# ---------- model ----------

@dataclass(frozen=True)
class FunctionInfo:
    qualname: str
    lineno: int
    end_lineno: int


# ---------- tiny helpers (≤10 lines each) ----------

def _pyver() -> str:
    return sys.version.split()[0]

def _pkgver(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "unknown"

def _end(n: ast.AST) -> int:
    return getattr(n, "end_lineno", getattr(n, "lineno", 0))

def _qname(prefix: tuple[str, ...], name: str) -> str:
    return ".".join((*prefix, name)) if prefix else name

def _is_named(n: ast.AST) -> bool:
    return isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))

def _child_pairs(node: ast.AST, parents: tuple[str, ...]) -> list[tuple[ast.AST, tuple[str, ...]]]:
    return [
        (ch, (*parents, ch.name)) if _is_named(ch) else (ch, parents)
        for ch in ast.iter_child_nodes(node)
    ]

def _walk_with_parents(root: ast.AST) -> Iterator[tuple[ast.AST, tuple[str, ...]]]:
    stack: list[tuple[ast.AST, tuple[str, ...]]] = [(root, ())]
    while stack:
        node, parents = stack.pop()
        yield node, parents
        stack.extend(_child_pairs(node, parents))

def _collect(tree: ast.AST) -> list[FunctionInfo]:
    funcs = (
        FunctionInfo(_qname(parents, n.name), n.lineno, _end(n))
        for n, parents in _walk_with_parents(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    )
    return sorted(funcs, key=lambda f: (f.lineno, f.end_lineno))

def _read(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"))

def _ensure_file(path: Path) -> None:
    if not path.exists() or not path.is_file():
        typer.secho(f"Not a file: {path}", fg=typer.colors.RED)
        raise typer.Exit(2)

def _render(funcs: Iterable[FunctionInfo], src: Path) -> None:
    table = Table(title=f"Functions in {src}")
    table.add_column("Function")
    table.add_column("Lines", justify="right")
    table.add_column("Start", justify="right")
    table.add_column("End", justify="right")
    for f in funcs:
        lines = f.end_lineno - f.lineno + 1
        table.add_row(f.qualname, str(lines), str(f.lineno), str(f.end_lineno))
    console.print(table)

def _render_env() -> None:
    console.print(
        f"[dim]Python { _pyver() } | typer { _pkgver('typer') } | rich { _pkgver('rich') }[/dim]"
    )


# ---------- CLI ----------

@app.command()
def main(file: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True)) -> None:
    """List functions and their line counts in a Python source file."""
    _ensure_file(file)
    funcs = _collect(_read(file))
    if not funcs:
        console.print(f"[yellow]No functions found in {file}[/yellow]")
        _render_env()
        raise typer.Exit(0)
    _render(funcs, file)
    _render_env()

if __name__ == "__main__":
    app()

