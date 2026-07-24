"""Command-line interface for imgconvert."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from imgconvert.converter import SUPPORTED_EXT, _output_ext, batch_convert, convert


def _parse_ext(raw: str) -> str:
    ext = raw if raw.startswith(".") else f".{raw}"
    ext = ext.lower()
    if ext == ".jpeg":
        ext = ".jpg"
    if ext not in SUPPORTED_EXT:
        choices = ", ".join(sorted(SUPPORTED_EXT))
        raise argparse.ArgumentTypeError(
            f"Unsupported format: {raw}. Choices: {choices}"
        )
    return ext


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="imgconvert",
        description="Convert between PDF, ICO, JPG, and PNG formats.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # Single file conversion
    single = sub.add_parser("convert", help="Convert a single file")
    single.add_argument("source", type=Path, help="Source file path")
    single.add_argument("target", type=Path, nargs="?", help="Output file path")
    single.add_argument(
        "-f", "--format",
        type=_parse_ext,
        help="Target format extension (e.g. .png). Required if target path is omitted.",
    )
    single.add_argument(
        "-q", "--quality",
        type=int,
        default=95,
        help="JPEG quality (1-100, default: 95)",
    )

    # Batch conversion
    batch = sub.add_parser("batch", help="Batch convert multiple files")
    batch.add_argument("sources", type=Path, nargs="+", help="Source file(s)")
    batch.add_argument(
        "-f", "--format",
        type=_parse_ext,
        required=True,
        help="Target format extension (e.g. .png)",
    )
    batch.add_argument(
        "-o", "--output",
        type=Path,
        default=Path("."),
        help="Output directory (default: current directory)",
    )
    batch.add_argument(
        "-q", "--quality",
        type=int,
        default=95,
        help="JPEG quality (1-100, default: 95)",
    )

    args = parser.parse_args(argv)

    try:
        if args.command == "convert":
            _handle_single(args)
        elif args.command == "batch":
            _handle_batch(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def _handle_single(args: argparse.Namespace) -> None:
    source: Path = args.source

    if args.target:
        target = args.target
    elif args.format:
        target = source.with_suffix(args.format)
    else:
        print("Error: must specify either target path or --format", file=sys.stderr)
        sys.exit(1)

    out = convert(source, target, args.quality)
    print(f"Converted: {source} -> {out}")


def _handle_batch(args: argparse.Namespace) -> None:
    out = batch_convert(args.sources, args.output, args.format, args.quality)
    for p in out:
        print(f"Converted: {p}")
    print(f"Done. {len(out)} file(s) converted.")


if __name__ == "__main__":
    main()
