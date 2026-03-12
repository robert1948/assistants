"""Command routing and optional JSON-backed state for the CLI assistant."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TodoItem:
    id: int
    text: str
    done: bool = False


_TODOS: list[TodoItem] = []
_STATE_FILE: Path | None = None


def configure_state_file(path: str | None) -> None:
    """Configure optional JSON state file used by todo commands."""
    global _STATE_FILE
    _STATE_FILE = Path(path) if path else None
    _load_todos()


def reset_state() -> None:
    """Reset in-memory state for deterministic tests."""
    _TODOS.clear()


def _load_todos() -> None:
    _TODOS.clear()
    if _STATE_FILE is None or not _STATE_FILE.exists():
        return

    try:
        raw = json.loads(_STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return

    if not isinstance(raw, list):
        return

    for item in raw:
        if not isinstance(item, dict):
            continue
        todo_id = item.get("id")
        text = item.get("text")
        done = item.get("done", False)
        if isinstance(todo_id, int) and todo_id > 0 and isinstance(text, str):
            _TODOS.append(TodoItem(id=todo_id, text=text, done=bool(done)))


def _save_todos() -> None:
    if _STATE_FILE is None:
        return

    try:
        _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        payload = [
            {"id": item.id, "text": item.text, "done": item.done} for item in _TODOS
        ]
        _STATE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError:
        # Keep assistant responsive even if persistence cannot be written.
        pass


def _handle_todo(todo_payload: str) -> str:
    if not todo_payload:
        return "Please provide todo text after '/todo'."

    if todo_payload == "list":
        if not _TODOS:
            return "No TODO items."
        return "\n".join(
            f"[{'x' if item.done else ' '}] {item.id}. {item.text}" for item in _TODOS
        )

    if todo_payload.startswith("done"):
        remainder = todo_payload[len("done") :].strip()
        if not remainder:
            return "Please provide a todo id after '/todo done'."
        if not remainder.isdigit():
            return "Todo id must be a positive integer."

        todo_id = int(remainder)
        if todo_id <= 0:
            return "Todo id must be a positive integer."

        for item in _TODOS:
            if item.id == todo_id:
                if item.done:
                    return f"TODO #{todo_id} is already done."
                item.done = True
                _save_todos()
                return f"TODO #{todo_id} marked done."
        return f"TODO #{todo_id} not found."

    next_id = len(_TODOS) + 1
    _TODOS.append(TodoItem(id=next_id, text=todo_payload))
    _save_todos()
    return f"TODO #{next_id} captured: {todo_payload}"


def respond(user_input: str) -> str:
    """Return deterministic responses for baseline CLI assistant commands."""
    normalized = user_input.strip()

    if not normalized:
        return "Please provide a message."

    if normalized == "/help":
        return (
            "Usage: text | /todo <item> | /todo list | /todo done <id> | "
            "/upper <text> | /lower <text> | /reverse <text>."
        )

    if normalized.startswith("/todo"):
        if _STATE_FILE is not None:
            _load_todos()
        todo_payload = normalized[len("/todo") :].strip()
        return _handle_todo(todo_payload)

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
