#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "pillow>=11.0",
# ]
# ///
from __future__ import annotations

import hashlib
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Callable, Iterable, Sequence, TextIO

from PIL import Image, UnidentifiedImageError

HASH_PREFIX_LENGTH = 8

FetchFn = Callable[[], bytes]
NowFn = Callable[[], datetime]


@dataclass(frozen=True)
class ClipboardFetcher:
    name: str
    fetch: FetchFn


def _run_command(args: Sequence[str]) -> bytes:
    result = subprocess.run(
        args,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    data = result.stdout
    if not data:
        raise RuntimeError(f"{args[0]} produced no output")
    return data


def _iter_wl_paste_commands() -> Iterable[Sequence[str]]:
    for mime in ("image/png", "image/jpeg"):
        yield ("wl-paste", "--no-newline", "--type", mime)


def _wl_paste_fetch() -> bytes:
    return _run_first(_iter_wl_paste_commands())


def _iter_xclip_commands() -> Iterable[Sequence[str]]:
    for mime in ("image/png", "image/jpeg"):
        yield ("xclip", "-selection", "clipboard", "-t", mime, "-o")


def _xclip_fetch() -> bytes:
    return _run_first(_iter_xclip_commands())


def _pngpaste_fetch() -> bytes:
    return _run_command(("pngpaste", "-"))


def _attempt_command(
    command: Sequence[str],
) -> tuple[bytes | None, str | None]:
    try:
        return _run_command(command), None
    except FileNotFoundError:
        return None, f"{command[0]}: not installed"
    except Exception as exc:  # noqa: BLE001 - collapsing command failures
        return None, f"{command[0]}: {exc}"


def _command_result(command: Sequence[str]) -> tuple[bytes | None, str]:
    output, error = _attempt_command(command)
    return output, error or f"{command[0]} failed"


def _run_first(commands: Iterable[Sequence[str]]) -> bytes:
    attempts = tuple(_command_result(command) for command in commands)
    for output, _ in attempts:
        if output is not None:
            return output
    detail = (
        "; ".join(error for _, error in attempts if error) or "no commands executed"
    )
    raise RuntimeError(detail)


DEFAULT_FETCHERS: tuple[ClipboardFetcher, ...] = (
    ClipboardFetcher("wl-paste", _wl_paste_fetch),
    ClipboardFetcher("xclip", _xclip_fetch),
    ClipboardFetcher("pngpaste", _pngpaste_fetch),
)


def _ensure_fetchers(
    fetchers: Sequence[ClipboardFetcher] | None,
) -> tuple[ClipboardFetcher, ...]:
    if fetchers:
        return tuple(fetchers)
    return DEFAULT_FETCHERS


def _attempt_fetch(
    fetcher: ClipboardFetcher,
) -> tuple[bytes | None, str | None]:
    try:
        return fetcher.fetch(), None
    except FileNotFoundError:
        return None, f"{fetcher.name}: not installed"
    except Exception as exc:  # noqa: BLE001 - collapsing fetch errors
        return None, f"{fetcher.name}: {exc}"


def _fetch_result(fetcher: ClipboardFetcher) -> tuple[bytes | None, str]:
    payload, error = _attempt_fetch(fetcher)
    return payload, error or f"{fetcher.name} failed"


def read_clipboard_image(
    fetchers: Sequence[ClipboardFetcher] | None = None,
) -> bytes:
    """Return clipboard image bytes using the first working fetcher."""
    attempts = tuple(_fetch_result(fetcher) for fetcher in _ensure_fetchers(fetchers))
    for payload, _ in attempts:
        if payload is not None:
            return payload
    detail = (
        "; ".join(error for _, error in attempts if error)
        or "no clipboard commands were tried"
    )
    raise RuntimeError(f"Failed to read clipboard image: {detail}")


def _load_image(payload: bytes) -> Image.Image:
    try:
        return Image.open(BytesIO(payload))
    except (UnidentifiedImageError, OSError) as exc:
        raise RuntimeError("Failed to decode clipboard image payload") from exc


def convert_to_jpeg(payload: bytes) -> bytes:
    """Convert arbitrary image bytes to JPEG."""
    with _load_image(payload) as image:
        rgb_image = image.convert("RGB")
        buffer = BytesIO()
        rgb_image.save(buffer, format="JPEG", optimize=True, quality=95)
    return buffer.getvalue()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def build_filename(content: bytes, moment: datetime) -> str:
    """Return the output filename for the provided content at the given time."""
    stamp = moment.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest = hashlib.sha256(content).hexdigest()[:HASH_PREFIX_LENGTH]
    return f".temp_{stamp}_{digest}.jpg"


def copy_clipboard_image(
    *,
    fetchers: Sequence[ClipboardFetcher] | None = None,
    now: NowFn = _utc_now,
    output_dir: Path | None = None,
    stdout: TextIO = sys.stdout,
) -> Path:
    """Fetch clipboard image bytes, save them, and print the output path."""
    jpeg = _clipboard_jpeg(fetchers)
    path = _persist_image(jpeg, output_dir, now())
    _announce_path(path, stdout)
    return path


def _clipboard_jpeg(
    fetchers: Sequence[ClipboardFetcher] | None,
) -> bytes:
    payload = read_clipboard_image(fetchers)
    return convert_to_jpeg(payload)


def _persist_image(jpeg: bytes, output_dir: Path | None, moment: datetime) -> Path:
    base = output_dir or Path.cwd()
    path = base / build_filename(jpeg, moment)
    path.write_bytes(jpeg)
    return path


def _announce_path(path: Path, stdout: TextIO) -> None:
    stdout.write(f"{path.resolve()}\n")
    stdout.flush()


def main(stdout: TextIO = sys.stdout, stderr: TextIO = sys.stderr) -> int:
    """Entry point for the script CLI."""
    try:
        copy_clipboard_image(stdout=stdout)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
