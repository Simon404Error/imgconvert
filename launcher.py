"""GUI launcher for imgconvert - double-click to start the web UI.

Opens the browser automatically after the server starts.
Close this window to stop the server.
"""
from __future__ import annotations

import socket
import sys
import threading
import webbrowser
from pathlib import Path

# Ensure local package is importable when running from source or bundled .exe
_here = Path(__file__).resolve().parent
if str(_here) not in sys.path:
    sys.path.insert(0, str(_here))


def _find_free_port(start: int = 5080) -> int:
    """Find a free TCP port starting from *start*."""
    for port in range(start, start + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return start


def _open_browser(url: str) -> None:
    import time
    time.sleep(1.2)
    webbrowser.open(url)


def main() -> None:
    from imgconvert.web import app

    host = "127.0.0.1"
    port = _find_free_port()
    url = f"http://{host}:{port}"

    threading.Thread(target=_open_browser, args=(url,), daemon=True).start()

    print("=" * 48)
    print("  图片格式转换工具")
    print(f"  浏览器访问: {url}")
    print("  关闭此窗口即可停止服务")
    print("=" * 48)

    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()
