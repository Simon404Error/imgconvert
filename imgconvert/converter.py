"""Core conversion engine for image format conversion."""

from __future__ import annotations

import io
import struct
from collections import deque
from pathlib import Path
from typing import Sequence

import fitz  # pymupdf
from PIL import Image, ImageChops, ImageDraw

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


def process_images(
    images: Sequence[Image.Image],
    crop: tuple[int, int, int, int] | None = None,
    corner_radius: int = 0,
    cutout: bool = False,
    cutout_tolerance: int = 30,
) -> list[Image.Image]:
    """Apply optional image processing steps to each loaded image."""
    result: list[Image.Image] = []
    for img in images:
        if crop is not None:
            left, top, right, bottom = crop
            if left < 0 or top < 0 or right <= left or bottom <= top:
                raise ValueError(f"Invalid crop box: {crop}")
            if right > img.width or bottom > img.height:
                raise ValueError(
                    f"Crop box {crop} exceeds image size {img.size}"
                )
            img = img.crop((left, top, right, bottom))

        if corner_radius > 0:
            img = apply_rounded_corners(img, corner_radius, trim=True)

        if cutout:
            img = apply_cutout_background(img, cutout_tolerance)

        result.append(img)
    return result


def apply_rounded_corners(
    img: Image.Image, radius: int, trim: bool = False
) -> Image.Image:
    """Round the corners of an image, preserving existing transparency."""
    img = img.convert("RGBA")
    if trim:
        img = _trim_background_margin(img)
    w, h = img.size
    radius = max(0, min(int(radius), w // 2, h // 2))
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=255)
    if "A" in img.getbands():
        mask = ImageChops.multiply(img.getchannel("A"), mask)
    img.putalpha(mask)
    return img


def _near_background(px: tuple[int, ...], bg: tuple[int, int, int], tol: int) -> bool:
    return (
        abs(px[0] - bg[0]) + abs(px[1] - bg[1]) + abs(px[2] - bg[2])
    ) <= tol * 3


def _trim_background_margin(
    img: Image.Image, tolerance: int = 24
) -> Image.Image:
    """Crop the uniform background margin around the image content."""
    img = img.convert("RGBA")
    w, h = img.size
    pixels = img.load()

    corners = [
        pixels[0, 0],
        pixels[w - 1, 0],
        pixels[0, h - 1],
        pixels[w - 1, h - 1],
    ]
    bg = tuple(sum(c[i] for c in corners) // 4 for i in range(3))
    bg_alpha = sum(c[3] for c in corners) // 4

    min_x, min_y = w, h
    max_x, max_y = -1, -1
    for y in range(h):
        for x in range(w):
            p = pixels[x, y]
            if p[3] > 8 and (
                bg_alpha < 8 or not _near_background(p, bg, tolerance)
            ):
                if x < min_x:
                    min_x = x
                if x > max_x:
                    max_x = x
                if y < min_y:
                    min_y = y
                if y > max_y:
                    max_y = y

    if max_x >= min_x:
        return img.crop((min_x, min_y, max_x + 1, max_y + 1))
    return img


def apply_cutout_background(
    img: Image.Image, tolerance: int = 30
) -> Image.Image:
    """Remove the background connected to image edges (flood fill)."""
    img = img.convert("RGBA")
    w, h = img.size
    pixels = img.load()

    corners = [
        pixels[0, 0],
        pixels[w - 1, 0],
        pixels[0, h - 1],
        pixels[w - 1, h - 1],
    ]
    bg = tuple(sum(c[i] for c in corners) // 4 for i in range(3))

    visited = bytearray(w * h)
    queue: deque[tuple[int, int]] = deque()

    def seed(x: int, y: int) -> None:
        idx = y * w + x
        if visited[idx] == 0 and _near_background(pixels[x, y], bg, tolerance):
            visited[idx] = 1
            queue.append((x, y))

    for x in range(w):
        seed(x, 0)
        seed(x, h - 1)
    for y in range(h):
        seed(0, y)
        seed(w - 1, y)

    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < w and 0 <= ny < h:
                idx = ny * w + nx
                if visited[idx] == 0 and _near_background(
                    pixels[nx, ny], bg, tolerance
                ):
                    visited[idx] = 1
                    queue.append((nx, ny))

    alpha = img.getchannel("A")
    alpha_pixels = alpha.load()
    for y in range(h):
        row = y * w
        for x in range(w):
            if visited[row + x]:
                alpha_pixels[x, y] = 0
    img.putalpha(alpha)
    return img


def convert(
    source: Path,
    target: Path,
    quality: int = 95,
    crop: tuple[int, int, int, int] | None = None,
    corner_radius: int = 0,
    cutout: bool = False,
    cutout_tolerance: int = 30,
) -> Path:
    """Convert a source file to the target format.

    Args:
        source: Path to the source file.
        target: Desired output path. The extension determines the output format.
        quality: JPEG quality (1-100), only used for JPEG output. Defaults to 95.
        crop: Optional (left, top, right, bottom) pixel crop box.
        corner_radius: Optional rounded corner radius in pixels.
        cutout: Remove the background connected to image edges.
        cutout_tolerance: Color-distance tolerance for background removal.

    Returns:
        The output Path.
    """
    if not source.is_file():
        raise FileNotFoundError(f"Source file not found: {source}")

    src_fmt = _resolve_format(source.suffix)
    dst_fmt = _resolve_format(target.suffix)

    processing = (
        crop is not None
        or corner_radius > 0
        or cutout
    )
    if src_fmt == dst_fmt and not processing:
        raise ValueError(f"Source and target formats are the same ({src_fmt})")

    images = _load_images(source)
    images = process_images(
        images,
        crop=crop,
        corner_radius=corner_radius,
        cutout=cutout,
        cutout_tolerance=cutout_tolerance,
    )

    if dst_fmt == "PDF":
        _write_pdf(images, target)
    elif dst_fmt == "ICO":
        _write_ico(images, target, corner_radius=corner_radius)
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


def _write_ico(
    images: list[Image.Image],
    target: Path,
    corner_radius: int = 0,
) -> None:
    """Write a modern ICO file with PNG-compressed entries.

    Pillow re-resizes from the first image when saving ICO, which loses the
    per-size rounded corners. Write the binary directly so every size keeps
    its exact processed pixels.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    img = images[0].convert("RGBA")

    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    entries: list[tuple[int, int, bytes]] = []
    max_dim = max(img.width, img.height)

    for width, height in sizes:
        if width <= img.width and height <= img.height:
            resized = img.resize((width, height), Image.LANCZOS)
            if corner_radius > 0:
                scaled = max(1, round(corner_radius * width / max_dim))
                resized = apply_rounded_corners(resized, scaled)
            _zero_transparent_rgb(resized)
            buf = io.BytesIO()
            resized.save(buf, "PNG")
            entries.append((width, height, buf.getvalue()))

    if not entries:
        resized = img.resize((256, 256), Image.LANCZOS)
        if corner_radius > 0:
            scaled = max(1, round(corner_radius * 256 / max_dim))
            resized = apply_rounded_corners(resized, scaled)
        _zero_transparent_rgb(resized)
        buf = io.BytesIO()
        resized.save(buf, "PNG")
        entries.append((256, 256, buf.getvalue()))

    header_size = 6 + len(entries) * 16
    out = bytearray()
    out += struct.pack("<HHH", 0, 1, len(entries))
    offset = header_size
    for width, height, data in entries:
        out += struct.pack(
            "<BBBBHHII",
            width if width < 256 else 0,
            height if height < 256 else 0,
            0,
            0,
            1,
            32,
            len(data),
            offset,
        )
        offset += len(data)
    for _, _, data in entries:
        out += data
    target.write_bytes(out)


def _zero_transparent_rgb(img: Image.Image) -> Image.Image:
    """Set RGB of fully transparent pixels to black to avoid white halos."""
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if a == 0:
                px[x, y] = (0, 0, 0, 0)
    return img


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
    crop: tuple[int, int, int, int] | None = None,
    corner_radius: int = 0,
    cutout: bool = False,
    cutout_tolerance: int = 30,
) -> list[Path]:
    """Batch convert multiple files to the same target format.

    Returns a list of output paths.
    """
    out: list[Path] = []
    for src in sources:
        name = src.stem
        target = output_dir / f"{name}{_output_ext(target_fmt)}"
        convert(
            src,
            target,
            quality,
            crop=crop,
            corner_radius=corner_radius,
            cutout=cutout,
            cutout_tolerance=cutout_tolerance,
        )
        out.append(target)
    return out
