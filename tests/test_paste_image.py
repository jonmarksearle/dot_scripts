from __future__ import annotations

import datetime as dt
import io
from collections.abc import Callable
from pathlib import Path

import pytest
from PIL import Image

import paste_image


def test__copy_clipboard_image__empty_clipboard__fail(
    empty_clipboard_fetchers: tuple[paste_image.ClipboardFetcher, ...],
    copy_image: Callable[..., Path],
) -> None:
    with pytest.raises(RuntimeError, match=r"Nothing to paste"):
        copy_image(fetchers=empty_clipboard_fetchers)


def test__convert_to_jpeg__invalid_payload__fail(
    invalid_payload: bytes,
) -> None:
    with pytest.raises(RuntimeError, match=r"decode"):
        paste_image.convert_to_jpeg(invalid_payload)


@pytest.mark.parametrize(
    ("missing_dependency_fetchers", "expected_message"),
    (
        pytest.param(("wl-paste",), r"^wl-paste: not installed$", id="wl-paste"),
        pytest.param(("xclip",), r"^xclip: not installed$", id="xclip"),
        pytest.param(("pngpaste",), r"^pngpaste: not installed$", id="pngpaste"),
    ),
    indirect=("missing_dependency_fetchers",),
)
def test__copy_clipboard_image__missing_dependency__fail(
    missing_dependency_fetchers: tuple[paste_image.ClipboardFetcher, ...],
    expected_message: str,
    copy_image: Callable[..., Path],
) -> None:
    with pytest.raises(RuntimeError, match=expected_message):
        copy_image(fetchers=missing_dependency_fetchers)


def test__copy_clipboard_image__writes_expected_file__success(
    copy_image: Callable[..., Path],
    success_fetchers: tuple[paste_image.ClipboardFetcher, ...],
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
    tmp_path: Path,
    stdout_buffer: io.StringIO,
) -> Callable[..., Path]:
    def _run(**kwargs) -> Path:
        return paste_image.copy_clipboard_image(
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
def empty_clipboard_fetchers() -> tuple[paste_image.ClipboardFetcher, ...]:
    def _empty_fetch() -> bytes:
        return b""

    return (paste_image.ClipboardFetcher("wl-paste", _empty_fetch),)


@pytest.fixture
def missing_dependency_fetchers(
    request: pytest.FixtureRequest,
    raise_helper: Callable[[Exception], Callable[[], bytes]],
) -> tuple[paste_image.ClipboardFetcher, ...]:
    names: tuple[str, ...] = request.param

    def _build(name: str) -> paste_image.ClipboardFetcher:
        return paste_image.ClipboardFetcher(
            name,
            raise_helper(FileNotFoundError(f"{name} missing")),
        )

    return tuple(_build(name) for name in names)


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
) -> tuple[paste_image.ClipboardFetcher, ...]:
    return (paste_image.ClipboardFetcher("fake", png_fetcher),)


@pytest.fixture
def fixed_time() -> Callable[[], dt.datetime]:
    def _now() -> dt.datetime:
        return dt.datetime(2025, 11, 16, 10, 5, tzinfo=dt.timezone.utc)

    return _now


def assert_saved_image(path: Path, stdout: io.StringIO, prefix: str) -> None:
    assert path.name.startswith(prefix)
    assert path.read_bytes().startswith(b"\xff\xd8")
    assert stdout.getvalue().strip() == str(path.resolve())
