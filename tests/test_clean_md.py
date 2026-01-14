from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest
from typer.testing import CliRunner

import clean_md


def _text(lines: str) -> str:
    return dedent(lines).lstrip("\n")


def _assert_clean(raw: str, expected: str) -> None:
    assert clean_md.clean_md_text(_text(raw)) == _text(expected)


def test__clean_md_text__fail__missing_title() -> None:
    with pytest.raises(ValueError, match="Missing title"):
        clean_md.clean_md_text("")


def test__clean__fail__no_md_files(tmp_path: Path) -> None:
    result = CliRunner().invoke(clean_md.app, ["clean", str(tmp_path)])
    assert result.exit_code != 0


def test__clean_md_text__success__keeps_title_updated_header_and_related() -> None:
    _assert_clean(
        """
        Title Line

        Skip this
        [Updated 07 Jul 2025](https://example.com/history/1)
        More nav
        # Header
        Body line
        {Account.webp}
        Related contentMore info
        Send feedback
        [Page A](https://example.com/a)
        Page A
        [Author A](https://home.atlassian.com/people/a)
        [Page B](https://example.com/b)
        Page B
        [Author B](https://home.atlassian.com/people/b)
        """,
        """
        Title Line

        [Updated 07 Jul 2025](https://example.com/history/1)

        # Header
        Body line

        Author A - [Page A](https://example.com/a)
        Author B - [Page B](https://example.com/b)
        """,
    )


def test__clean_md_text__success__removes_add_label_without_related() -> None:
    _assert_clean(
        """
        Title
        [Updated 01 Jan 2025](https://example.com/history/2)
        # Header
        Body line
        Add label
        """,
        """
        Title

        [Updated 01 Jan 2025](https://example.com/history/2)

        # Header
        Body line
        """,
    )


def test__clean_md_text__success__handles_related_without_add_label() -> None:
    _assert_clean(
        """
        Title
        # Header
        Body line
        Related contentMore info
        [Page A](https://example.com/a)
        Page A
        [Author A](https://home.atlassian.com/people/a)
        """,
        """
        Title

        # Header
        Body line

        Author A - [Page A](https://example.com/a)
        """,
    )


def test__clean_md_text__success__removes_boilerplate_assets() -> None:
    _assert_clean(
        """
        Title
        # Header
        Keep me
        {atl.site.logo}
        {default-space-logo-256.png}
        Another line
        """,
        """
        Title

        # Header
        Keep me
        Another line
        """,
    )


def test__clean_md_text__success__keeps_without_updated_line() -> None:
    _assert_clean(
        """
        Title
        Skip this
        # Header
        Body line
        """,
        """
        Title

        # Header
        Body line
        """,
    )


def test__clean_md_text__success__ignores_related_without_author() -> None:
    _assert_clean(
        """
        Title
        # Header
        Body line
        Related contentMore info
        [Page A](https://example.com/a)
        """,
        """
        Title

        # Header
        Body line
        """,
    )


def test__clean_md_text__success__removes_site_logo_lines() -> None:
    _assert_clean(
        """
        Title
        # Header
        {atl.site.logo}
        """,
        """
        Title

        # Header
        """,
    )


def test__clean_md_text__success__keeps_non_boilerplate_placeholders() -> None:
    _assert_clean(
        """
        Title
        # Header
        {image-20250101-010101.png}
        """,
        """
        Title

        # Header
        {image-20250101-010101.png}
        """,
    )


def test__clean_md_text__success__keeps_add_label_in_sentence() -> None:
    _assert_clean(
        """
        Title
        # Header
        Please add label to this section.
        """,
        """
        Title

        # Header
        Please add label to this section.
        """,
    )


def test__clean_md_text__success__ignores_author_before_page() -> None:
    _assert_clean(
        """
        Title
        # Header
        Related contentMore info
        [Author A](https://home.atlassian.com/people/a)
        [Page A](https://example.com/a)
        """,
        """
        Title

        # Header
        """,
    )


def test__clean_md_text__success__uses_title_when_no_hash_header() -> None:
    _assert_clean(
        """
        Title Line
        Edited 27 Oct 2025
        Random nav
        """,
        """
        Title Line

        Edited 27 Oct 2025

        # Title Line
        """,
    )


def test__clean_md_text__success__removes_non_ascii() -> None:
    _assert_clean(
        """
        Title
        # Header
        This ��� line has non-ascii.
        """,
        """
        Title

        # Header
        This line has non-ascii.
        """,
    )


def test__clean_md_text__success__prefers_updated_over_edited() -> None:
    _assert_clean(
        """
        Title
        Edited 01 Jan 2024
        [Updated 02 Feb 2025](https://example.com/history/9)
        # Header
        Body
        """,
        """
        Title

        [Updated 02 Feb 2025](https://example.com/history/9)

        # Header
        Body
        """,
    )


def test__clean_md_text__success__uses_first_related_section_only() -> None:
    _assert_clean(
        """
        Title
        # Header
        Related contentMore info
        [Page A](https://example.com/a)
        Page A
        [Author A](https://home.atlassian.com/people/a)
        Related contentMore info
        [Page B](https://example.com/b)
        Page B
        [Author B](https://home.atlassian.com/people/b)
        """,
        """
        Title

        # Header

        Author A - [Page A](https://example.com/a)
        """,
    )


def test__clean_md_text__success__keeps_table_spacing_with_non_ascii() -> None:
    _assert_clean(
        """
        Title
        # Header
        | A | B ��� C |
        """,
        """
        Title

        # Header
        | A | B   C |
        """,
    )


def test__remove_asset_files__success__ignores_missing(tmp_path: Path) -> None:
    paths = tuple(
        (tmp_path / name)
        for name in ("sample.Account.webp", "sample.drawlogo.svg", "keep.png")
    )
    _ = tuple(path.write_text("x") for path in paths)
    clean_md.remove_asset_files(tmp_path)
    assert tuple(p.exists() for p in paths) == (False, False, True)


def test__clean_md_text__success__uses_title_when_header_missing() -> None:
    _assert_clean(
        """
        Title
        No header
        """,
        """
        Title

        # Title
        """,
    )


def test__clean_md_text__success__related_line_with_extra_links() -> None:
    _assert_clean(
        """
        Title
        # Header
        Related contentMore info
        [Page A](https://example.com/a) and [Page B](https://example.com/b)
        Page A
        [Author A](https://home.atlassian.com/people/a)
        """,
        """
        Title

        # Header

        Author A - [Page B](https://example.com/b)
        """,
    )


def test__remove_asset_files__success__keeps_suffix_in_middle(tmp_path: Path) -> None:
    path = tmp_path / "sample.Account.webp.bak"
    path.write_text("x")
    clean_md.remove_asset_files(tmp_path)
    assert path.exists()
