from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

import mhtml2md


@pytest.fixture
def sample_mhtml_content() -> bytes:
    # A minimal MHTML-like structure for testing
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


def test__base_name__success() -> None:
    assert mhtml2md._base_name(Path("test.mhtml")) == "test"
    assert mhtml2md._base_name(Path("folder/my_file.MHTML")) == "my_file"


def test__safe_stem__success() -> None:
    assert mhtml2md._safe_stem("File/Name*With:Chars") == "File_Name_With_Chars"
    assert mhtml2md._safe_stem("  Spaces  ") == "Spaces"


def test__extract_images_and_html__success(sample_mhtml_content: bytes) -> None:
    extracts = mhtml2md._extract_images_and_html(sample_mhtml_content)
    assert "<h1>Hello World</h1>" in extracts.html
    images = list(extracts.images)
    assert len(images) == 1
    assert images[0].content_id == "image1"
    assert images[0].content_type == "image/png"


def test__convert_mhtml_to_md__success(
    tmp_path: Path, sample_mhtml_content: bytes
) -> None:
    mhtml_file = tmp_path / "test.mhtml"
    mhtml_file.write_bytes(sample_mhtml_content)
    out_dir = tmp_path / "out"

    bundle = mhtml2md.convert_mhtml_to_md(mhtml_file, out_dir)

    assert bundle.md_path.exists()
    md_content = bundle.md_path.read_text()
    assert "# Hello World" in md_content
    # The image reference should be replaced by a placeholder format {base.name.ext}
    assert "{test.test_image.png}" in md_content

    image_files = list(bundle.image_paths)
    assert len(image_files) == 1
    assert image_files[0].suffix == ".png"
    assert "test_image" in image_files[0].name
