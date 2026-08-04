"""Command-line interface for imgconvert."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from imgconvert.converter import (
    SUPPORTED_EXT,
    _output_ext,
    batch_convert,
    convert,
)


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


def _parse_crop(raw: str) -> tuple[int, int, int, int]:
    parts = [p.strip() for p in raw.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError(
            "--crop must be four numbers: left,top,right,bottom"
        )
    try:
        return tuple(int(p) for p in parts)  # type: ignore[return-value]
    except ValueError:
        raise argparse.ArgumentTypeError(
            "--crop values must be integers: left,top,right,bottom"
        )


def _add_processing_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--crop",
        type=_parse_crop,
        metavar="L,T,R,B",
        help="Crop box in pixels, e.g. --crop 10,10,200,200",
    )
    parser.add_argument(
        "--radius",
        type=int,
        default=0,
        help="Rounded corner radius in pixels (0 disables)",
    )
    parser.add_argument(
        "--cutout",
        action="store_true",
        help="Remove the background connected to image edges",
    )
    parser.add_argument(
        "--cutout-tolerance",
        type=int,
        default=30,
        help="Background removal tolerance (default: 30)",
    )


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
    _add_processing_args(single)

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
    _add_processing_args(batch)

    # Web server
    serve = sub.add_parser("serve", help="Start the web UI server")
    serve.add_argument(
        "-H", "--host",
        default="127.0.0.1",
        help="Bind address (default: 127.0.0.1)",
    )
    serve.add_argument(
        "-p", "--port",
        type=int,
        default=5080,
        help="Listen port (default: 5080)",
    )
    serve.add_argument(
        "--ngrok",
        action="store_true",
        help="Create a public ngrok tunnel so anyone on the internet can access the web UI",
    )

    args = parser.parse_args(argv)

    try:
        if args.command == "convert":
            _handle_single(args)
        elif args.command == "batch":
            _handle_batch(args)
        elif args.command == "serve":
            _handle_serve(args)
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

    out = convert(
        source,
        target,
        args.quality,
        crop=args.crop,
        corner_radius=args.radius,
        cutout=args.cutout,
        cutout_tolerance=args.cutout_tolerance,
    )
    print(f"Converted: {source} -> {out}")


def _handle_batch(args: argparse.Namespace) -> None:
    out = batch_convert(
        args.sources,
        args.output,
        args.format,
        args.quality,
        crop=args.crop,
        corner_radius=args.radius,
        cutout=args.cutout,
        cutout_tolerance=args.cutout_tolerance,
    )
    for p in out:
        print(f"Converted: {p}")
    print(f"Done. {len(out)} file(s) converted.")


def _handle_serve(args: argparse.Namespace) -> None:
    from imgconvert.web import run_server

    if args.ngrok:
        # ngrok tunnel always binds to 127.0.0.1
        print(f"Starting web UI at http://127.0.0.1:{args.port}")
        run_server(host="127.0.0.1", port=args.port, ngrok=True)
    else:
        if args.host == "127.0.0.1":
            print(f"Starting web UI at http://{args.host}:{args.port}")
            print("提示: 使用 -H 0.0.0.0 允许局域网访问，使用 --ngrok 创建公网隧道")
        else:
            print(f"Starting web UI at http://{args.host}:{args.port}")
        run_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
