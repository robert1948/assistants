"""Command routing and in-memory state for the minimal CLI assistant."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TodoItem:
    id: int
    text: str
    done: bool = False


_TODOS: list[TodoItem] = []


def reset_state() -> None:
    """Reset in-memory state for deterministic tests."""
    _TODOS.clear()


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
                return f"TODO #{todo_id} marked done."
        return f"TODO #{todo_id} not found."

    next_id = len(_TODOS) + 1
    _TODOS.append(TodoItem(id=next_id, text=todo_payload))
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
