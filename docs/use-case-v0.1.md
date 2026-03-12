# Use Case v0.1: CLI Prompt Assistant

## Goal

Provide a minimal command-line assistant that accepts a single user message and returns a structured response. This creates a stable baseline for future assistant workflows.

## Inputs

- A user-provided text string.
- Optional command-like prefixes:
  - `/help`
  - `/todo <text>`
  - `/todo list`
  - `/todo done <id>`
  - `/upper <text>`
  - `/lower <text>`
  - `/reverse <text>`

## Outputs

- For `/help`: usage guidance.
- For `/todo <text>`: acknowledgement of captured todo text.
- For `/todo list`: current todo items with status markers.
- For `/todo done <id>`: mark a todo as done.
- For `/upper <text>`: transformed uppercase text.
- For `/lower <text>`: transformed lowercase text.
- For `/reverse <text>`: reversed text.
- For general text: normalized echo response.
- For empty input: prompt requesting a valid message.
- For unsupported slash commands: deterministic unknown-command message.

## Constraints

- Must run with standard Python only (no third-party dependencies).
- Must be testable with built-in `unittest`.
- Must provide deterministic output for CI checks.
- TODO state is in-memory only (process-local) for this milestone.

## Acceptance Criteria

- Running `python -m src.assistant_echo "hello"` returns a valid response.
- Automated tests pass with `python -m unittest discover -s tests -p "test_*.py"`.
- CI executes tests on push and pull request events.
