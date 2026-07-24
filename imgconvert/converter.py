"""Core conversion engine for image format conversion."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Sequence

import fitz  # pymupdf
from PIL import Image

SUPPORTED_EXT = {".pdf", ".ico", ".jpg", ".jpeg", ".png"}


def _resolve_format(ext: str) -> str:
    ext = ext.lower()
    if ext in (".jpg", ".jpeg"):
        return "JPEG"
    if ext == ".png":
        return "PNG"
    if ext == ".ico":
        return "ICO"
    if ext == ".pdf":
        return "PDF"
    raise ValueError(f"Unsupported extension: {ext}")


def _output_ext(fmt: str) -> str:
    fmt = fmt.lstrip(".").upper()
    if fmt == "JPEG" or fmt == "JPG":
        return ".jpg"
    if fmt == "PNG":
        return ".png"
    if fmt == "ICO":
        return ".ico"
    return f".{fmt.lower()}"


def _load_images(path: Path) -> list[Image.Image]:
    fmt = _resolve_format(path.suffix)
    images: list[Image.Image] = []

    if fmt == "PDF":
        doc = fitz.open(path)
        for page in doc:
            pix = page.get_pixmap(dpi=200)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(img)
        doc.close()
    elif fmt == "ICO":
        img = Image.open(path)
        # ICO may contain multiple sizes; load all frames
        try:
            while True:
                images.append(img.copy().convert("RGBA"))
                img.seek(img.tell() + 1)
        except EOFError:
            pass
    else:
        img = Image.open(path)
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")
        images.append(img)

    return images


def convert(source: Path, target: Path, quality: int = 95) -> Path:
    """Convert a source file to the target format.

    Args:
        source: Path to the source file.
        target: Desired output path. The extension determines the output format.
        quality: JPEG quality (1-100), only used for JPEG output. Defaults to 95.

    Returns:
        The output Path.
    """
    if not source.is_file():
        raise FileNotFoundError(f"Source file not found: {source}")

    src_fmt = _resolve_format(source.suffix)
    dst_fmt = _resolve_format(target.suffix)

    if src_fmt == dst_fmt:
        raise ValueError(f"Source and target formats are the same ({src_fmt})")

    # Load all images from source
    images = _load_images(source)

    if dst_fmt == "PDF":
        _write_pdf(images, target)
    elif dst_fmt == "ICO":
        _write_ico(images, target)
    else:
        _write_image(images, target, dst_fmt, quality)

    return target


def _write_pdf(images: list[Image.Image], target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    rgb_images = []
    for img in images:
        if img.mode == "RGBA":
            # Composite onto white background
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3])
            rgb_images.append(bg)
        elif img.mode != "RGB":
            rgb_images.append(img.convert("RGB"))
        else:
            rgb_images.append(img)

    if len(rgb_images) == 1:
        rgb_images[0].save(target, "PDF", resolution=200.0)
    else:
        rgb_images[0].save(
            target,
            "PDF",
            save_all=True,
            append_images=rgb_images[1:],
            resolution=200.0,
        )


def _write_ico(images: list[Image.Image], target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    # Use the first image for ICO, resized to 256x256 max
    img = images[0]
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    # Standard ICO sizes
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    ico_images = []
    for size in sizes:
        if size[0] <= img.width and size[1] <= img.height:
            ico_images.append(img.resize(size, Image.LANCZOS))

    if not ico_images:
        ico_images.append(img.resize((256, 256), Image.LANCZOS))

    ico_images[0].save(target, "ICO", sizes=[(i.width, i.height) for i in ico_images])


def _write_image(
    images: list[Image.Image], target: Path, fmt: str, quality: int
) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    img = images[0]
    if fmt == "JPEG":
        if img.mode == "RGBA":
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3])
            img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")
        img.save(target, fmt, quality=quality)
    elif fmt == "PNG":
        if img.mode not in ("RGBA", "RGB"):
            img = img.convert("RGBA")
        img.save(target, fmt)


def batch_convert(
    sources: Sequence[Path],
    output_dir: Path,
    target_fmt: str,
    quality: int = 95,
) -> list[Path]:
    """Batch convert multiple files to the same target format.

    Returns a list of output paths.
    """
    out: list[Path] = []
    for src in sources:
        name = src.stem
        target = output_dir / f"{name}{_output_ext(target_fmt)}"
        convert(src, target, quality)
        out.append(target)
    return out
