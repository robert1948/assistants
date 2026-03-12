"""Minimal CLI assistant implementation."""

from __future__ import annotations

import argparse


def respond(user_input: str) -> str:
    """Return deterministic responses for baseline CLI assistant commands."""
    normalized = user_input.strip()

    if not normalized:
        return "Please provide a message."

    if normalized == "/help":
        return (
            "Usage: text | /todo <item> | /upper <text> | "
            "/lower <text> | /reverse <text>."
        )

    if normalized.startswith("/todo"):
        todo_text = normalized[len("/todo") :].strip()
        if not todo_text:
            return "Please provide todo text after '/todo'."
        return f"TODO captured: {todo_text}"

    if normalized.startswith("/upper"):
        payload = normalized[len("/upper") :].strip()
        if not payload:
            return "Please provide text after '/upper'."
        return payload.upper()

    if normalized.startswith("/lower"):
        payload = normalized[len("/lower") :].strip()
        if not payload:
            return "Please provide text after '/lower'."
        return payload.lower()

    if normalized.startswith("/reverse"):
        payload = normalized[len("/reverse") :].strip()
        if not payload:
            return "Please provide text after '/reverse'."
        return payload[::-1]

    if normalized.startswith("/"):
        command = normalized.split(maxsplit=1)[0]
        return f"Unknown command: {command}. Try /help."

    return f"You said: {normalized}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Minimal CLI assistant")
    parser.add_argument("message", nargs="?", default="", help="User message")
    args = parser.parse_args()

    print(respond(args.message))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
