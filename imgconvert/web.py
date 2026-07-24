"""Flask web server providing a visual UI for image format conversion."""

from __future__ import annotations

import io
import os
import sys
import tempfile
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file

from imgconvert.converter import SUPPORTED_EXT, _resolve_format, convert

app = Flask(__name__)

FMT_TO_EXT = {
    "png": ".png",
    "jpg": ".jpg",
    "jpeg": ".jpg",
    "ico": ".ico",
    "pdf": ".pdf",
}

MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".ico": "image/x-icon",
    ".pdf": "application/pdf",
}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/convert", methods=["POST"])
def do_convert():
    file = request.files.get("file")
    target_fmt = request.form.get("format", "png")
    quality = int(request.form.get("quality", 95))

    if not file or not file.filename:
        return jsonify({"error": "未选择文件"}), 400

    src_ext = Path(file.filename).suffix.lower()
    if src_ext not in SUPPORTED_EXT:
        choices = ", ".join(sorted(SUPPORTED_EXT))
        return jsonify({"error": f"不支持的格式: {src_ext}，支持: {choices}"}), 400

    out_ext = FMT_TO_EXT.get(target_fmt)
    if not out_ext:
        return jsonify({"error": f"不支持的目标格式: {target_fmt}"}), 400

    if src_ext == out_ext or (src_ext == ".jpeg" and out_ext == ".jpg"):
        return jsonify({"error": "源格式与目标格式相同，无需转换"}), 400

    with tempfile.NamedTemporaryFile(suffix=src_ext, delete=False) as tmp_in:
        file.save(tmp_in.name)
        src = Path(tmp_in.name)

    out = src.with_suffix(out_ext)

    try:
        result = convert(src, out, quality)
        with open(result, "rb") as f:
            data = f.read()
        return send_file(
            io.BytesIO(data),
            mimetype=MIME_TYPES.get(out_ext, "application/octet-stream"),
            as_attachment=True,
            download_name=result.name,
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"转换失败: {e}"}), 500
    finally:
        for p in (src, out):
            if p.exists():
                try:
                    os.unlink(p)
                except OSError:
                    pass


def _start_ngrok(port: int) -> str | None:
    """Start an ngrok tunnel and return the public URL, or None on failure."""
    try:
        from pyngrok import ngrok
    except ImportError:
        print("pyngrok 未安装，请执行: pip install pyngrok", file=sys.stderr)
        return None

    try:
        tunnel = ngrok.connect(port, "http")
        return str(tunnel.public_url)
    except Exception as e:
        print(f"ngrok 隧道创建失败: {e}", file=sys.stderr)
        print("请确认: 1) ngrok 已安装  2) 已配置 auth token (ngrok config add-authtoken <token>)",
              file=sys.stderr)
        return None


def run_server(
    host: str = "127.0.0.1",
    port: int = 5080,
    debug: bool = False,
    ngrok: bool = False,
) -> None:
    """Start the Flask development server, optionally with ngrok public tunnel."""
    public_url: str | None = None

    if ngrok:
        print("正在创建 ngrok 公网隧道...")
        public_url = _start_ngrok(port)
        if public_url:
            print(f"公网地址: {public_url}")

    if host in ("0.0.0.0", "::"):
        print(f"局域网地址: http://<本机IP>:{port}")

    app.run(host=host, port=port, debug=debug)
