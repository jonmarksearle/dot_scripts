#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "typer>=0.12",
#   "beautifulsoup4",
#   "markdownify",
#   "lxml",
# ]
# ///
from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from pathlib import Path

import typer
from bs4 import BeautifulSoup
from bs4.element import Tag
from markdownify import markdownify as html_to_md  # type: ignore[import-untyped]

app = typer.Typer(add_completion=False, no_args_is_help=True)

## Process Classes


@dataclass(frozen=True, slots=True)
class MhtmlImage:
    content_id: str | None
    content_location: str | None
    filename_hint: str | None
    content_type: str
    payload: bytes


@dataclass(frozen=True, slots=True)
class ImageWritePlan:
    disambiguated_name: str
    ext: str
    payload: bytes
    placeholder_tail: str


@dataclass(slots=True)
class ReplacementState:
    lookup: dict[str, MhtmlImage]
    used: dict[str, int]
    saved_by_src: dict[str, str]


## class: MarkdownBundle


@dataclass(frozen=True, slots=True)
class MarkdownBundle:
    md_path: Path

    @property
    def image_paths(self) -> Iterator[Path]:
        return (
            p
            for p in self.md_path.parent.glob(f"{self.md_path.stem}.*")
            if p.suffix.lower() != ".md"
        )


## class: MessageExtracts


def _looks_like_image_filename(name: str) -> bool:
    return Path(name).suffix.lower() in {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".bmp",
        ".tif",
        ".tiff",
        ".svg",
    }


def _is_image_part(part: EmailMessage) -> bool:
    maintype = (part.get_content_maintype() or "").lower()
    if maintype == "image":
        return True

    filename = _filename_from_headers(part)
    return bool(filename and _looks_like_image_filename(filename))


def _is_extracted_image(part: EmailMessage) -> bool:
    return (not part.is_multipart()) and _is_image_part(part)


def _extract_images(msg: EmailMessage) -> Iterator[MhtmlImage]:
    return (_to_image(p) for p in _iter_parts(msg) if _is_extracted_image(p))


def _extract_images_and_html(mhtml_bytes: bytes) -> MessageExtracts:
    return MessageExtracts(_parse_mhtml(mhtml_bytes))


@dataclass(frozen=True, slots=True)
class MessageExtracts:
    msg: EmailMessage

    @property
    def html(self) -> str:
        return _extract_html(self.msg)

    @property
    def images(self) -> Iterator[MhtmlImage]:
        return _extract_images(self.msg)


## Filename Functions

_MAX_FILENAME_BYTES = 255
_HASH_SUFFIX_BYTES = 8


def _filename_bytes(value: str) -> int:
    return len(value.encode("utf-8"))


def _hash_suffix(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:_HASH_SUFFIX_BYTES]


def _truncate_utf8(value: str, max_bytes: int) -> str:
    if max_bytes <= 0:
        return ""
    encoded = value.encode("utf-8")
    if len(encoded) <= max_bytes:
        return value
    return encoded[:max_bytes].decode("utf-8", errors="ignore").rstrip()


def _name_budget(base: str, ext: str) -> int:
    return _MAX_FILENAME_BYTES - _filename_bytes(f"{base}..{ext}")


def _base_budget_for_md() -> int:
    return _MAX_FILENAME_BYTES - _filename_bytes(".md")


def _base_budget_for_image(ext: str, name: str) -> int:
    min_name = _hash_suffix(name)
    return _MAX_FILENAME_BYTES - _filename_bytes(f".{min_name}.{ext}")


def _shorten_name_with_hash(name: str, budget: int) -> str:
    suffix = f"-{_hash_suffix(name)}"
    suffix_bytes = _filename_bytes(suffix)
    if budget <= suffix_bytes:
        return _truncate_utf8(_hash_suffix(name), budget)
    head = _truncate_utf8(name, budget - suffix_bytes)
    return f"{head}{suffix}"


def _limited_base_name(base: str, budget: int) -> str:
    if _filename_bytes(base) <= budget:
        return base
    return _shorten_name_with_hash(base, budget)


def _limited_md_base(base: str) -> str:
    return _limited_base_name(base, _base_budget_for_md())


def _limited_image_base(base: str, name: str, ext: str) -> str:
    return _limited_base_name(base, _base_budget_for_image(ext, name))


def _limited_image_name(base: str, name: str, ext: str) -> str:
    budget = _name_budget(base, ext)
    if _filename_bytes(name) <= budget:
        return name
    return _shorten_name_with_hash(name, budget)


def _base_name(input_path: Path) -> str:
    return input_path.name[: -len(input_path.suffix)]


def _normalise_key(value: str) -> str:
    return value.strip().lower()


def _safe_stem(name: str) -> str:
    name = name.strip()
    name = re.sub(r"[\/\\:\*\?\"<>\|]+", "_", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip(" ._")


def _strip_angle_brackets(value: str | None) -> str | None:
    if not value:
        return None
    return value.strip().lstrip("<").rstrip(">").strip()


def _filename_from_headers(part: EmailMessage) -> str | None:
    filename = part.get_filename()
    if filename:
        return filename

    content_location = part.get("Content-Location")
    if not content_location:
        return None

    tail = content_location.split("/")[-1].split("?")[0]
    return tail if "." in tail else None


def _guess_ext(img: MhtmlImage) -> str:
    if img.filename_hint:
        ext = Path(img.filename_hint).suffix.lower().lstrip(".")
        if ext:
            return "jpg" if ext == "jpeg" else ext

    if "/" not in img.content_type:
        return "bin"

    subtype = img.content_type.split("/", 1)[1].lower()
    if subtype == "svg+xml":
        return "svg"
    return "jpg" if subtype == "jpeg" else subtype


def _tail(content_location: str | None) -> str:
    if not content_location:
        return ""
    return content_location.split("/")[-1].split("?")[0]


def _best_image_name(img: MhtmlImage, fallback: str) -> str:
    if img.filename_hint:
        return _safe_stem(Path(img.filename_hint).stem)
    if img.content_location:
        return _safe_stem(Path(_tail(img.content_location)).stem)
    return fallback


def _iter_parts(msg: EmailMessage) -> Iterator[EmailMessage]:
    if msg.is_multipart():
        yield from msg.walk()
        return
    yield msg


def _to_image(part: EmailMessage) -> MhtmlImage:
    raw = part.get_payload(decode=True)
    payload = raw if isinstance(raw, (bytes, bytearray)) else b""
    return MhtmlImage(
        content_id=_strip_angle_brackets(part.get("Content-ID")),
        content_location=part.get("Content-Location"),
        filename_hint=_filename_from_headers(part),
        content_type=(part.get_content_type() or "application/octet-stream").lower(),
        payload=payload,
    )


def _parse_mhtml(mhtml_bytes: bytes) -> EmailMessage:
    return BytesParser(policy=policy.default).parsebytes(mhtml_bytes)


def _html_parts(msg: EmailMessage) -> Iterable[str]:
    return (
        part.get_content()
        for part in _iter_parts(msg)
        if not part.is_multipart()
        and (part.get_content_type() or "").lower() == "text/html"
    )


def _extract_html(msg: EmailMessage) -> str:
    html = "\n".join(h for h in _html_parts(msg) if h).strip()
    if not html:
        raise ValueError("No HTML part found in MHTML (expected Confluence export).")
    return html


def _replacement_state(images: Iterable[MhtmlImage]) -> ReplacementState:
    return ReplacementState(lookup=_image_lookup(images), used={}, saved_by_src={})


def _image_lookup(images: Iterable[MhtmlImage]) -> dict[str, MhtmlImage]:
    lookup: dict[str, MhtmlImage] = {}
    for img in images:
        _add_image_keys(lookup, img)
    return lookup


def _add_image_keys(lookup: dict[str, MhtmlImage], img: MhtmlImage) -> None:
    for key in _image_keys(img):
        lookup[key] = img


def _image_keys(img: MhtmlImage) -> Iterable[str]:
    return (_normalise_key(raw) for raw in _candidate_image_keys(img))


def _candidate_image_keys(img: MhtmlImage) -> Iterable[str]:
    yield from _cid_keys(img)
    yield from _location_keys(img)
    yield from _filename_keys(img)


def _cid_keys(img: MhtmlImage) -> Iterable[str]:
    if not img.content_id:
        return
    yield f"cid:{img.content_id}"
    yield img.content_id


def _location_keys(img: MhtmlImage) -> Iterable[str]:
    if not img.content_location:
        return
    yield img.content_location

    tail = _tail(img.content_location)
    if tail:
        yield tail


def _filename_keys(img: MhtmlImage) -> Iterable[str]:
    if not img.filename_hint:
        return
    yield img.filename_hint
    yield Path(img.filename_hint).name


def _replace_images_with_placeholders(
    html: str,
    images: Iterable[MhtmlImage],
    base: str,
    outdir: Path,
) -> str:
    soup = BeautifulSoup(html, "lxml")
    state = _replacement_state(images)
    _rewrite_img_tags(soup, state, base, outdir)
    return str(soup)


def _rewrite_img_tags(
    soup: BeautifulSoup, state: ReplacementState, base: str, outdir: Path
) -> None:
    for tag in soup.find_all("img"):
        _rewrite_one_img_tag(tag, state, base, outdir)


def _rewrite_one_img_tag(
    tag: Tag, state: ReplacementState, base: str, outdir: Path
) -> None:
    src = _img_src(tag)
    if not src:
        return
    tag.replace_with(_replacement_for_src(tag, src, state, base, outdir))


def _img_src(tag: Tag) -> str:
    src = tag.get("src")
    if not isinstance(src, str):
        return ""
    return src.strip()


def _replacement_for_src(
    tag: Tag,
    src: str,
    state: ReplacementState,
    base: str,
    outdir: Path,
) -> str:
    cached = state.saved_by_src.get(src)
    if cached:
        return f"{{{cached}}}"

    img = _match_image(src, state.lookup)
    if not img:
        return _placeholder_fallback(tag)

    plan = _build_write_plan(tag, img, state.used, base)
    _execute_write_plan(outdir, base, plan)

    state.saved_by_src[src] = plan.placeholder_tail
    return f"{{{plan.placeholder_tail}}}"


def _match_image(src: str, lookup: dict[str, MhtmlImage]) -> MhtmlImage | None:
    for key in _src_match_keys(src):
        hit = lookup.get(key)
        if hit:
            return hit
    return None


def _src_match_keys(src: str) -> Iterable[str]:
    cleaned = src.strip()
    if not cleaned:
        return

    yield _normalise_key(cleaned)

    if cleaned.startswith("cid:"):
        yield _normalise_key(cleaned.replace("cid:", "", 1))


def _placeholder_fallback(tag: Tag) -> str:
    raw = _first_tag_attr(tag, ("data-image-name", "data-filename", "alt")) or "image"
    return f"{{{_safe_stem(str(raw))}}}"


def _build_write_plan(
    tag: Tag, img: MhtmlImage, used: dict[str, int], base: str
) -> ImageWritePlan:
    ext = _guess_ext(img)
    base_name = _preferred_image_name(tag, img)
    disambiguated = _next_disambiguated_name(base_name, used)
    safe_name = _limited_image_name(base, disambiguated, ext)
    tail = f"{safe_name}.{ext}"
    return ImageWritePlan(
        disambiguated_name=safe_name,
        ext=ext,
        payload=img.payload,
        placeholder_tail=tail,
    )


def _preferred_image_name(tag: Tag, img: MhtmlImage) -> str:
    return _tag_image_name(tag) or _image_metadata_name(img) or "image"


def _tag_image_name(tag: Tag) -> str:
    raw = _first_tag_attr(tag, ("data-image-name", "data-filename", "alt"))
    return _safe_stem(raw) if raw else ""


def _image_metadata_name(img: MhtmlImage) -> str:
    return _best_image_name(img, fallback="")


def _first_tag_attr(tag: Tag, keys: tuple[str, ...]) -> str:
    for key in keys:
        val = tag.get(key)
        if val:
            return str(val)
    return ""


def _next_disambiguated_name(base: str, used: dict[str, int]) -> str:
    n = used.get(base, 0) + 1
    used[base] = n
    return base if n == 1 else f"{base} ({n})"


def _execute_write_plan(outdir: Path, base: str, plan: ImageWritePlan) -> None:
    (outdir / _image_filename(base, plan.disambiguated_name, plan.ext)).write_bytes(
        plan.payload
    )


def _image_filename(base: str, name: str, ext: str) -> str:
    safe_base = _limited_image_base(base, name, ext)
    safe_name = _limited_image_name(safe_base, name, ext)
    return f"{safe_base}.{safe_name}.{ext}"


def _html_to_markdown(html: str) -> str:
    return html_to_md(html, heading_style="ATX")


def _postprocess_markdown(md: str) -> str:
    cleaned = md.replace("\r\n", "\n")
    cleaned = re.sub(r"\n{4,}", "\n\n\n", cleaned).strip()
    return f"{cleaned}\n"


def _write_markdown(outdir: Path, base: str, md: str) -> Path:
    path = outdir / f"{base}.md"
    path.write_text(_postprocess_markdown(md), encoding="utf-8")
    return path


def convert_mhtml_to_md(input_path: Path, outdir: Path) -> MarkdownBundle:
    outdir.mkdir(parents=True, exist_ok=True)
    base = _limited_md_base(_base_name(input_path))

    extracted = _extract_images_and_html(input_path.read_bytes())
    rewritten = _replace_images_with_placeholders(
        extracted.html, extracted.images, base, outdir
    )
    md_path = _write_markdown(outdir, base, _html_to_markdown(rewritten))
    return MarkdownBundle(md_path)


@app.command()
def convert(
    mhtml: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    outdir: Path | None = typer.Option(
        None, help="Output directory (default: alongside input)."
    ),
) -> None:
    """Convert a Confluence .mhtml export into one .md + extracted images."""
    target_dir = outdir or mhtml.parent
    bundle = convert_mhtml_to_md(mhtml, target_dir)

    typer.echo(f"Wrote: {bundle.md_path}")
    for p in bundle.image_paths:
        typer.echo(f"Image: {p.name}")


if __name__ == "__main__":
    app()
