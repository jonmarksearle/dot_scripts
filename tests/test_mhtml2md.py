from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

import mhtml2md


@pytest.fixture
def sample_mhtml_bytes() -> bytes:
    return dedent(
        """\
        MIME-Version: 1.0
        Content-Type: multipart/related; boundary="boundary-1"

        --boundary-1
        Content-Type: text/html; charset="utf-8"

        <html>
          <body>
            <h1>Hello World</h1>
            <img src="cid:image1" alt="test image">
          </body>
        </html>

        --boundary-1
        Content-Type: image/png
        Content-ID: <image1>
        Content-Transfer-Encoding: base64

        iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==
        --boundary-1--
        """
    ).encode("utf-8")


@pytest.fixture
def no_html_mhtml_bytes() -> bytes:
    return dedent(
        """\
        MIME-Version: 1.0
        Content-Type: multipart/related; boundary="boundary-1"

        --boundary-1
        Content-Type: image/png
        Content-ID: <image1>
        Content-Transfer-Encoding: base64

        iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==
        --boundary-1--
        """
    ).encode("utf-8")


@pytest.fixture
def sample_mhtml_file(tmp_path: Path, sample_mhtml_bytes: bytes) -> Path:
    mhtml_file = tmp_path / "test.mhtml"
    mhtml_file.write_bytes(sample_mhtml_bytes)
    return mhtml_file


@pytest.fixture
def out_dir(tmp_path: Path) -> Path:
    return tmp_path / "out"


@pytest.fixture
def extracts(sample_mhtml_bytes: bytes) -> mhtml2md.MessageExtracts:
    return mhtml2md._extract_images_and_html(sample_mhtml_bytes)


@pytest.fixture
def extracted_images(extracts: mhtml2md.MessageExtracts) -> list[mhtml2md.MhtmlImage]:
    return list(extracts.images)


@pytest.fixture
def bundle(sample_mhtml_file: Path, out_dir: Path) -> mhtml2md.MarkdownBundle:
    return mhtml2md.convert_mhtml_to_md(sample_mhtml_file, out_dir)


@pytest.fixture
def md_content(bundle: mhtml2md.MarkdownBundle) -> str:
    return bundle.md_path.read_text()


@pytest.fixture
def image_paths(bundle: mhtml2md.MarkdownBundle) -> list[Path]:
    return list(bundle.image_paths)


def test__extract_images_and_html__fail__no_html_part(
    no_html_mhtml_bytes: bytes,
) -> None:
    with pytest.raises(ValueError, match="No HTML part found"):
        mhtml2md._extract_images_and_html(no_html_mhtml_bytes).html


def test__convert_mhtml_to_md__fail__missing_input(out_dir: Path) -> None:
    missing = out_dir / "missing.mhtml"
    with pytest.raises(FileNotFoundError):
        mhtml2md.convert_mhtml_to_md(missing, out_dir)


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("test.mhtml", "test"),
        ("folder/my_file.MHTML", "my_file"),
    ],
)
def test__base_name__success(path: str, expected: str) -> None:
    assert mhtml2md._base_name(Path(path)) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("File/Name*With:Chars", "File_Name_With_Chars"),
        ("  Spaces  ", "Spaces"),
    ],
)
def test__safe_stem__success(raw: str, expected: str) -> None:
    assert mhtml2md._safe_stem(raw) == expected


def test__extract_images_and_html__success__html(
    extracts: mhtml2md.MessageExtracts,
) -> None:
    assert "<h1>Hello World</h1>" in extracts.html


def test__extract_images_and_html__success__image_count(
    extracted_images: list[mhtml2md.MhtmlImage],
) -> None:
    assert len(extracted_images) == 1


def test__extract_images_and_html__success__image_metadata(
    extracted_images: list[mhtml2md.MhtmlImage],
) -> None:
    image = extracted_images[0]
    assert (image.content_id, image.content_type) == ("image1", "image/png")


def test__convert_mhtml_to_md__success__md_path_exists(
    bundle: mhtml2md.MarkdownBundle,
) -> None:
    assert bundle.md_path.exists()


def test__convert_mhtml_to_md__success__heading(md_content: str) -> None:
    assert "# Hello World" in md_content


def test__convert_mhtml_to_md__success__placeholder(md_content: str) -> None:
    assert "{test image.png}" in md_content


def test__convert_mhtml_to_md__success__image_paths(image_paths: list[Path]) -> None:
    assert [path.name for path in image_paths] == ["test.test image.png"]
