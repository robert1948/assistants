"""Minimal CLI assistant implementation for v0.1."""

from __future__ import annotations

import argparse


def respond(user_input: str) -> str:
    """Return deterministic responses for the baseline CLI assistant."""
    normalized = user_input.strip()

    if not normalized:
        return "Please provide a message."

    if normalized == "/help":
        return "Usage: provide text or '/todo <item>' for simple capture."

    if normalized.startswith("/todo"):
        todo_text = normalized[len("/todo") :].strip()
        if not todo_text:
            return "Please provide todo text after '/todo'."
        return f"TODO captured: {todo_text}"

    return f"You said: {normalized}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Minimal CLI assistant")
    parser.add_argument("message", nargs="?", default="", help="User message")
    args = parser.parse_args()

    print(respond(args.message))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
