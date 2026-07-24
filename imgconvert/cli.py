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

    out = convert(source, target, args.quality)
    print(f"Converted: {source} -> {out}")


def _handle_batch(args: argparse.Namespace) -> None:
    out = batch_convert(args.sources, args.output, args.format, args.quality)
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
