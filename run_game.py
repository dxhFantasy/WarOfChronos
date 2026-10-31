from __future__ import annotations

import argparse
import sys
import threading
import webbrowser

import uvicorn

from server.app import app


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="WarOfChronos 本地/局域网服务器")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址，默认 0.0.0.0")
    parser.add_argument("--port", type=int, default=8000, help="监听端口，默认 8000")
    parser.add_argument("--no-browser", action="store_true", help="不自动打开浏览器")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    url = f"http://127.0.0.1:{args.port}/"
    print(f"WarOfChronos: {url}")
    print(f"局域网访问: http://<本机局域网IP>:{args.port}/")
    if getattr(sys, "frozen", False) and not args.no_browser:
        threading.Timer(1.5, webbrowser.open, args=(url,)).start()
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
