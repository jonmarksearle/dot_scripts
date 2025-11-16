from __future__ import annotations

import datetime as dt
import io
from collections.abc import Callable
from pathlib import Path

import pytest
from PIL import Image

import copyImage


def test__copy_clipboard_image__no_fetchers_succeed__fail(
    failure_fetchers: tuple[copyImage.ClipboardFetcher, ...],
    copy_image: Callable[..., Path],
) -> None:
    with pytest.raises(RuntimeError, match=r"wl-paste.+pngpaste"):
        copy_image(fetchers=failure_fetchers)


def test__convert_to_jpeg__invalid_payload__fail(
    invalid_payload: bytes,
) -> None:
    with pytest.raises(RuntimeError, match=r"decode"):
        copyImage.convert_to_jpeg(invalid_payload)


def test__copy_clipboard_image__writes_expected_file__success(
    copy_image: Callable[..., Path],
    success_fetchers: tuple[copyImage.ClipboardFetcher, ...],
    stdout_buffer: io.StringIO,
    fixed_time: Callable[[], dt.datetime],
) -> None:
    path = copy_image(fetchers=success_fetchers, now=fixed_time)
    assert_saved_image(path, stdout_buffer, ".temp_20251116T100500Z_")


@pytest.fixture
def stdout_buffer() -> io.StringIO:
    return io.StringIO()


@pytest.fixture
def copy_image(
    tmp_path: pytest.Path,
    stdout_buffer: io.StringIO,
) -> Callable[..., Path]:
    def _run(**kwargs) -> Path:
        return copyImage.copy_clipboard_image(
            output_dir=tmp_path,
            stdout=stdout_buffer,
            **kwargs,
        )

    return _run


@pytest.fixture
def raise_helper() -> Callable[[Exception], Callable[[], bytes]]:
    def _build(error: Exception) -> Callable[[], bytes]:
        def _inner() -> bytes:
            raise error

        return _inner

    return _build


@pytest.fixture
def failure_fetchers(
    raise_helper: Callable[[Exception], Callable[[], bytes]],
) -> tuple[copyImage.ClipboardFetcher, ...]:
    return (
        copyImage.ClipboardFetcher(
            "wl-paste", raise_helper(FileNotFoundError("missing"))
        ),
        copyImage.ClipboardFetcher(
            "pngpaste", raise_helper(RuntimeError("empty clipboard"))
        ),
    )


@pytest.fixture
def invalid_payload() -> bytes:
    return b"not image data"


@pytest.fixture
def png_payload() -> bytes:
    stream = io.BytesIO()
    Image.new("RGB", (1, 1), color="red").save(stream, format="PNG")
    return stream.getvalue()


@pytest.fixture
def png_fetcher(png_payload: bytes) -> Callable[[], bytes]:
    def _fetch() -> bytes:
        return png_payload

    return _fetch


@pytest.fixture
def success_fetchers(
    png_fetcher: Callable[[], bytes],
) -> tuple[copyImage.ClipboardFetcher, ...]:
    return (copyImage.ClipboardFetcher("fake", png_fetcher),)


@pytest.fixture
def fixed_time() -> Callable[[], dt.datetime]:
    def _now() -> dt.datetime:
        return dt.datetime(2025, 11, 16, 10, 5, tzinfo=dt.timezone.utc)

    return _now


def assert_saved_image(path: Path, stdout: io.StringIO, prefix: str) -> None:
    assert path.name.startswith(prefix)
    assert path.read_bytes().startswith(b"\xff\xd8")
    assert stdout.getvalue().strip() == str(path.resolve())
