"""CLI entrypoint for the minimal assistant."""

from __future__ import annotations

import argparse
import os

from src.command_router import configure_state_file, reset_state, respond

__all__ = ["configure_state_file", "main", "respond", "reset_state"]

VERSION = "0.2.0"


def _resolve_state_file(cli_state_file: str | None) -> str | None:
    """Resolve state-file preference from CLI arg, env var, then default."""
    if cli_state_file is not None:
        return cli_state_file or None

    env_state_file = os.getenv("ASSISTANTS_STATE_FILE")
    if env_state_file is not None:
        return env_state_file or None

    return ".assistant_todos.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Minimal CLI assistant")
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print CLI version and exit.",
    )
    parser.add_argument(
        "--health",
        action="store_true",
        help="Run a lightweight health check and exit.",
    )
    parser.add_argument(
        "--state-file",
        default=None,
        help=(
            "Path to todo state JSON file (set empty value to disable persistence). "
            "If omitted, ASSISTANTS_STATE_FILE is used when set."
        ),
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode for multi-command sessions.",
    )
    parser.add_argument("message", nargs="?", default="", help="User message")
    args = parser.parse_args()

    if args.version:
        print(f"assistants-cli {VERSION}")
        return 0

    if args.health:
        print("ok")
        return 0

    configure_state_file(_resolve_state_file(args.state_file))

    if args.interactive:
        print("Interactive mode. Type /exit to quit.")
        while True:
            try:
                raw = input("> ").strip()
            except EOFError:
                print("\nGoodbye.")
                return 0
            if raw == "/exit":
                print("Goodbye.")
                return 0
            print(respond(raw))

    print(respond(args.message))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
