"""CLI entrypoint for the minimal assistant."""

from __future__ import annotations

import argparse

from src.command_router import reset_state, respond

__all__ = ["main", "respond", "reset_state"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Minimal CLI assistant")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode to keep in-memory state across commands.",
    )
    parser.add_argument("message", nargs="?", default="", help="User message")
    args = parser.parse_args()

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
