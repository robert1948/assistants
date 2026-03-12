# Changelog

All notable changes to this project are documented in this file.

## Unreleased

### Added

- CLI subprocess integration tests in `tests/test_cli_integration.py`.
- Coverage configuration in `.coveragerc`.
- Makefile target `coverage` for local coverage reports.
- Entrypoint-focused unit tests in `tests/test_assistant_entrypoint.py`.
- Bank statement ETL implementation blueprint in `docs/bank-agent-implementation.md`.
- PostgreSQL ingestion schema script in `sql/bank_ingestion_schema.sql`.
- ETL orchestration skeleton in `src/bank_statement_agent.py`.

### Changed

- CI now reports test coverage on the Python 3.12 matrix leg.
- `src/assistant_echo.py` refactored into parser/run/interactive helpers for testability.

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
