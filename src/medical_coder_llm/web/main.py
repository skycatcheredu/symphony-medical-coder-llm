from __future__ import annotations

import argparse
import sys

import uvicorn
from dotenv import load_dotenv

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


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
    args = parser.parse_args(argv)

    load_dotenv()

    _print_banner(args.host, args.port)

    uvicorn.run(
        "medical_coder_llm.web.app:app",
        host=args.host,
        port=args.port,
        factory=False,
    )


if __name__ == "__main__":
    main()
