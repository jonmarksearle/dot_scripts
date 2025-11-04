#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# PEP 723: Single-file script metadata
# https://peps.python.org/pep-0723/
#
# script:
#   description: Render stdin URLs to plain text via lynx.
#   dependencies:
#   python-version: ">=3.13"
#
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Callable, Iterable, Iterator, TextIO
from urllib import error, parse, request

DEFAULT_TIMEOUT = 15.0
URL_SCHEMES = {"http", "https"}

Fetch = Callable[[str], bytes]
Render = Callable[[bytes], str]


@dataclass(frozen=True)
class BrowseOutcome:
    url: str
    output: str | None
    error: str | None

    @property
    def is_error(self) -> bool:
        """Return True if this outcome represents an error."""
        return self.error is not None


def _iter_clean_lines(stream: Iterable[str]) -> Iterator[str]:
    for raw in stream:
        cleaned = raw.strip()
        if cleaned:
            yield cleaned


def _validate_url(raw: str) -> str:
    parsed = parse.urlparse(raw)
    if parsed.scheme.lower() not in URL_SCHEMES:
        msg = f"Error: unsupported URL '{raw}'. Provide an http(s) URL."
        raise ValueError(msg)
    return raw


def _default_fetch(url: str) -> bytes:
    with request.urlopen(url, timeout=DEFAULT_TIMEOUT) as response:  # nosec B310
        status = getattr(response, "status", 200)
        if 200 <= status < 300:
            return response.read()
        raise error.HTTPError(url, status, response.reason, response.headers, None)


def _default_render(payload: bytes) -> str:
    """Render HTML payload to plain text using lynx."""
    result = subprocess.run(
        ["lynx", "-dump", "-stdin"],
        input=payload,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.decode("utf-8", errors="replace")


def _fetch_payload(url: str, fetch: Fetch) -> tuple[bytes | None, str | None]:
    """Fetch URL payload or return error message."""
    try:
        return fetch(url), None
    except (error.HTTPError, error.URLError) as exc:
        msg = f"Error: failed to fetch '{url}': {exc}"
        return None, msg
    except FileNotFoundError as exc:
        return None, str(exc)


def _render_payload(
    url: str, payload: bytes, render: Render
) -> tuple[str | None, str | None]:
    """Render payload to text or return error message."""
    try:
        return render(payload), None
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode("utf-8", errors="replace")
        msg = f"Error: lynx failed while rendering '{url}': {stderr}"
        return None, msg


def _browse_url(url: str, fetch: Fetch, render: Render) -> BrowseOutcome:
    """Fetch and render a URL, returning the outcome."""
    payload, fetch_error = _fetch_payload(url, fetch)
    if fetch_error:
        return BrowseOutcome(url, None, fetch_error)
    assert payload is not None
    text, render_error = _render_payload(url, payload, render)
    if render_error:
        return BrowseOutcome(url, None, render_error)
    return BrowseOutcome(url, text, None)


def _outcome_for_raw(raw: str, fetch: Fetch, render: Render) -> BrowseOutcome:
    try:
        url = _validate_url(raw)
    except ValueError as exc:
        return BrowseOutcome(raw, None, str(exc))
    return _browse_url(url, fetch, render)


def browse_outcomes(
    stream: Iterable[str],
    *,
    fetch: Fetch = _default_fetch,
    render: Render = _default_render,
) -> Iterator[BrowseOutcome]:
    """Yield browse outcomes for each supported URL in the stream."""
    for raw in _iter_clean_lines(stream):
        yield _outcome_for_raw(raw, fetch, render)


def ensure_dependencies() -> None:
    """Verify required external binaries are available."""
    for binary in ("lynx",):
        if shutil.which(binary) is None:
            msg = f"Required dependency '{binary}' not found in PATH"
            raise FileNotFoundError(msg)


def _write_outcome(outcome: BrowseOutcome, stdout: TextIO, stderr: TextIO) -> int:
    """Write outcome to appropriate stream and return exit code."""
    if outcome.is_error:
        print(outcome.error, file=stderr)
        return 1
    text = outcome.output or ""
    print(f"URL: {outcome.url}", file=stdout)
    end = "" if text.endswith("\n") else "\n"
    print(text, file=stdout, end=end)
    print(file=stdout)
    return 0


def main(
    stdin: Iterable[str] = sys.stdin,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> int:
    """Render stdin URLs to plain text via lynx."""
    ensure_dependencies()
    exit_code = 0
    for outcome in browse_outcomes(stdin):
        exit_code = max(exit_code, _write_outcome(outcome, stdout, stderr))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
