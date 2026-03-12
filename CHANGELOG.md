# Changelog

All notable changes to this project are documented in this file.

## 0.2.0 - 2026-03-12

### Added

- JSON-backed todo persistence through `--state-file`.
- CLI diagnostics: `--health` and `--version`.
- Interactive mode for multi-command sessions.
- Makefile targets: `run-persistent`, `health`, and `version`.
- CI matrix testing across Python 3.10, 3.11, and 3.12.
- Router-focused persistence tests in `tests/test_command_router.py`.

### Changed

- Command routing moved into `src/command_router.py` for clearer separation.
- Todo workflow expanded with `/todo list` and `/todo done <id>`.
- State-file resolution now supports `ASSISTANTS_STATE_FILE`.

### Fixed

- Malformed JSON state files are handled safely and treated as empty state.
