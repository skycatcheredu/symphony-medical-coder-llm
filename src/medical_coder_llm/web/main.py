from __future__ import annotations

import argparse
import socket
import sys
import threading
import time
import webbrowser

import uvicorn
from dotenv import load_dotenv

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
_BROWSER_OPEN_WAIT_S = 10.0
_BROWSER_POLL_INTERVAL_S = 0.1


def _print_banner(host: str, port: int) -> None:
    url = f"http://{host}:{port}"
    lines = [
        "=" * 62,
        "Medical Coder — local web server",
        "",
        f"  Open this address in your web browser:  {url}",
        "",
        "  On Mac: paste that into Safari or Chrome’s address bar, then press Enter.",
        "",
        "  For local use only; do not expose this URL to the public internet.",
        "=" * 62,
    ]
    print("\n".join(lines), file=sys.stdout)


def _browser_open_url(bind_host: str, port: int) -> str:
    display_host = "127.0.0.1" if bind_host == "0.0.0.0" else bind_host
    return f"http://{display_host}:{port}"


def _tcp_probe_host(bind_host: str) -> str:
    return "127.0.0.1" if bind_host == "0.0.0.0" else bind_host


def _open_browser_when_ready(bind_host: str, port: int) -> None:
    url = _browser_open_url(bind_host, port)
    probe_host = _tcp_probe_host(bind_host)
    deadline = time.monotonic() + _BROWSER_OPEN_WAIT_S
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((probe_host, port), timeout=0.5):
                webbrowser.open(url)
                return
        except OSError:
            time.sleep(_BROWSER_POLL_INTERVAL_S)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the Medical Coder web UI (local).")
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"Bind address (default: {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not open a web browser automatically",
    )
    args = parser.parse_args(argv)

    load_dotenv()

    _print_banner(args.host, args.port)

    if not args.no_browser:
        threading.Thread(
            target=_open_browser_when_ready,
            args=(args.host, args.port),
            daemon=True,
        ).start()

    uvicorn.run(
        "medical_coder_llm.web.app:app",
        host=args.host,
        port=args.port,
        factory=False,
    )


if __name__ == "__main__":
    main()
