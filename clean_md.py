#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "typer>=0.12",
# ]
# ///
from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from itertools import takewhile
from pathlib import Path

import typer

app = typer.Typer(add_completion=False, no_args_is_help=True)

_ASSET_SUFFIXES = (
    "Account.webp",
    "Jon Searle.webp",
    "drawlogo.svg",
    "site.logo",
    "default-space-logo-256.png",
    "OZKP.png",
    "zenuml_logo.png",
    "wait.gif",
    "favicon.ico",
    "JIN.png",
    "thumbs up.png",
    "OZCET.png",
    "preview.svg",
    "89278e2b1046.png",
    "1d1f02c5bd78.webp",
    "3d389ff28503.webp",
    "0d861fe1cc44.png",
    "9d72-34a38eef8d76.png",
    "603f0f2581a8400068cdc067.png",
)

_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_UPDATED_RE = re.compile(r"^\[Updated .+\]\(.+\)$")
_EDITED_RE = re.compile(r"^Edited .+$")


def _iter_md_paths(target: Path) -> Iterator[Path]:
    if target.is_dir():
        yield from sorted(target.glob("*.md"))
        return
    if target.suffix.lower() == ".md":
        yield target


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _first_nonempty_line(lines: Iterable[str]) -> str:
    return next((line for line in lines if line.strip()), "")


def _date_line(lines: Iterable[str]) -> str | None:
    updated = next((line for line in lines if _UPDATED_RE.match(line.strip())), None)
    if updated:
        return updated
    return next((line for line in lines if _EDITED_RE.match(line.strip())), None)


def _clean_non_ascii(line: str) -> str:
    cleaned = re.sub(r"[^\x00-\x7F]+", " ", line)
    if "|" in cleaned:
        return cleaned
    match = re.match(r"^\s*", cleaned)
    leading = match.group(0) if match else ""
    body = cleaned[len(leading) :]
    body = re.sub(r"\s{2,}", " ", body)
    return f"{leading}{body}".rstrip()


def _normalise_lines(lines: Iterable[str]) -> Iterator[str]:
    return (_clean_non_ascii(line) for line in lines)


def _header_index(lines: tuple[str, ...]) -> int:
    return next((i for i, line in enumerate(lines) if line.startswith("# ")), -1)


def _intro_lines(title: str, updated: str | None, header: str) -> tuple[str, ...]:
    if updated:
        return (title, "", updated, "", header)
    return (title, "", header)


def _strip_to_header(lines: tuple[str, ...]) -> tuple[str, ...]:
    title = _first_nonempty_line(lines)
    updated = _date_line(lines)
    header_idx = _header_index(lines)
    if not title:
        raise ValueError("Missing title or header.")
    if header_idx < 0:
        return _intro_lines(title, updated, f"# {title}")
    header = lines[header_idx]
    return _intro_lines(title, updated, header) + lines[header_idx + 1 :]


def _is_add_label(line: str) -> bool:
    return line.strip() == "Add label"


def _is_asset_line(line: str) -> bool:
    return any(suffix in line for suffix in _ASSET_SUFFIXES)


def _filter_lines(lines: Iterable[str]) -> Iterator[str]:
    return (
        line for line in lines if not _is_add_label(line) and not _is_asset_line(line)
    )


def _index_of_line(lines: tuple[str, ...], target: str) -> int | None:
    return next((i for i, line in enumerate(lines) if line.strip() == target), None)


def _split_related(lines: Iterable[str]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    materialised = tuple(lines)
    idx = _index_of_line(materialised, "Related contentMore info")
    if idx is None:
        return materialised, ()
    return materialised[:idx], materialised[idx + 1 :]


def _links_in_line(line: str) -> Iterator[tuple[str, str]]:
    return ((m.group(1), m.group(2)) for m in _LINK_RE.finditer(line))


def _iter_links(lines: Iterable[str]) -> Iterator[tuple[str, str]]:
    return (link for line in lines for link in _links_in_line(line))


def _is_author_link(url: str) -> bool:
    return "home.atlassian.com" in url or "/people/" in url


def _iter_related_pairs(lines: Iterable[str]) -> Iterator[tuple[str, str, str]]:
    current = None
    for text, url in _iter_links(lines):
        if _is_author_link(url) and current:
            page_text, page_url = current
            current = None
            yield (text, page_text, page_url)
            continue
        if not _is_author_link(url):
            current = (text, url)


def _format_related(lines: Iterable[str]) -> tuple[str, ...]:
    pairs = tuple(_iter_related_pairs(_take_until_related_marker(lines)))
    if not pairs:
        return ()
    formatted = tuple(f"{author} - [{title}]({url})" for author, title, url in pairs)
    return ("",) + formatted


def _take_until_related_marker(lines: Iterable[str]) -> Iterator[str]:
    return takewhile(lambda line: line.strip() != "Related contentMore info", lines)


def _trim_trailing_blank_lines(lines: tuple[str, ...]) -> tuple[str, ...]:
    idx = next((i for i in range(len(lines), 0, -1) if lines[i - 1].strip()), 0)
    return lines[:idx]


def _clean_lines(lines: Iterable[str]) -> tuple[str, ...]:
    stripped = _strip_to_header(tuple(lines))
    filtered = _filter_lines(stripped)
    body, related = _split_related(filtered)
    return _trim_trailing_blank_lines(body + _format_related(related))


def clean_md_text(text: str) -> str:
    lines = _clean_lines(_normalise_lines(text.splitlines()))
    return f"{'\n'.join(lines)}\n"


def _is_asset_file(path: Path) -> bool:
    return path.is_file() and path.name.endswith(_ASSET_SUFFIXES)


def remove_asset_files(root: Path) -> None:
    for path in (path for path in root.iterdir() if _is_asset_file(path)):
        path.unlink(missing_ok=True)


def _clean_file(path: Path) -> None:
    _write_text(path, clean_md_text(_read_text(path)))


@app.command()
def clean(target: Path) -> None:
    """Clean Confluence Markdown exports in place."""
    md_paths = tuple(_iter_md_paths(target))
    if not md_paths:
        raise typer.BadParameter("No markdown files found.")
    for path in md_paths:
        _clean_file(path)
    remove_asset_files(target if target.is_dir() else target.parent)
    typer.echo(f"Cleaned {len(md_paths)} markdown files.")


if __name__ == "__main__":
    app()
