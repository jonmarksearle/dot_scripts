from __future__ import annotations

import io
import subprocess

import pytest

import browse


def test__browse_outcomes__invalid_scheme__fail() -> None:
    outcomes = list(browse.browse_outcomes(["ftp://example.com"]))
    assert outcomes[0].is_error
    error_msg = outcomes[0].error
    assert error_msg is not None
    assert "unsupported URL" in error_msg


def test__browse_outcomes__render_error__fail() -> None:
    def fake_fetch(_: str) -> bytes:
        return b"payload"

    def fake_render(_: bytes) -> str:
        raise subprocess.CalledProcessError(1, ["lynx"], stderr=b"boom")

    outcomes = list(
        browse.browse_outcomes(
            ["https://example.com"],
            fetch=fake_fetch,
            render=fake_render,
        )
    )
    assert outcomes[0].is_error
    error_msg = outcomes[0].error
    assert error_msg is not None
    assert "boom" in error_msg


def test__main__writes_errors__fail(monkeypatch: pytest.MonkeyPatch) -> None:
    stdout = io.StringIO()
    stderr = io.StringIO()
    outcome = browse.BrowseOutcome("https://example.com", None, "ouch")

    monkeypatch.setattr(browse, "ensure_dependencies", lambda: None)
    monkeypatch.setattr(browse, "browse_outcomes", lambda _: iter([outcome]))

    exit_code = browse.main(stdin=[], stdout=stdout, stderr=stderr)
    assert exit_code == 1
    assert "ouch" in stderr.getvalue()


def test__browse_outcomes__valid_url__success() -> None:
    def fake_fetch(_: str) -> bytes:
        return b"<html>"

    def fake_render(_: bytes) -> str:
        return "content\n"

    outcomes = list(
        browse.browse_outcomes(
            ["https://example.com"],
            fetch=fake_fetch,
            render=fake_render,
        )
    )
    assert not outcomes[0].is_error
    assert outcomes[0].output == "content\n"


def test__main__writes_success__success(monkeypatch: pytest.MonkeyPatch) -> None:
    stdout = io.StringIO()
    stderr = io.StringIO()
    body = "data\n"
    outcome = browse.BrowseOutcome("https://example.com", body, None)

    monkeypatch.setattr(browse, "ensure_dependencies", lambda: None)
    monkeypatch.setattr(browse, "browse_outcomes", lambda _: iter([outcome]))

    exit_code = browse.main(stdin=[], stdout=stdout, stderr=stderr)
    written = stdout.getvalue()

    assert exit_code == 0
    assert "URL: https://example.com" in written
    assert body in written
    assert stderr.getvalue() == ""
