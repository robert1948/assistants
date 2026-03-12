# assistants

Repository for building and experimenting with practical AI assistants.

## Overview

This project is an early-stage foundation for creating assistant workflows,
automation helpers, and supporting tooling. The immediate goal is to keep the
structure simple, documented, and ready for incremental feature delivery.

## Goals

- Build a reliable baseline project layout.
- Add repeatable quality checks through CI.
- Document purpose, scope, and contribution expectations.
- Ship a first usable v0.1 with one end-to-end assistant workflow.

## Non-goals (for now)

- Supporting every model provider from day one.
- Building a full UI before core assistant behavior is stable.
- Premature optimization of infrastructure.

## Project Structure

```text
assistants/
  docs/           # Project and design documentation
  src/            # Application/source code
  tests/          # Automated tests
```

## Getting Started

1. Clone the repository.
2. Review `docs/README.md` for documentation conventions.
3. Add source files under `src/` and tests under `tests/`.
4. Keep changes small and focused.

Quick run:

```bash
python3 -m src.assistant_echo "hello"
python3 -m src.assistant_echo --health
python3 -m src.assistant_echo --version
```

State-file precedence:

- `--state-file` CLI flag (highest priority)
- `ASSISTANTS_STATE_FILE` environment variable
- Default: `.assistant_todos.json`

Command examples:

```bash
python3 -m src.assistant_echo "/help"
python3 -m src.assistant_echo "/upper hello world"
python3 -m src.assistant_echo "/lower HeLLo"
python3 -m src.assistant_echo "/reverse abc123"
python3 -m src.assistant_echo "/todo buy milk"
```

Interactive mode (stateful todo flow):

```bash
python3 -m src.assistant_echo --interactive
# then enter:
/todo buy milk
/todo list
/todo done 1
/todo list
/exit
```

Persistent todo state file:

```bash
python3 -m src.assistant_echo --state-file .assistant_todos.json "/todo buy milk"
python3 -m src.assistant_echo --state-file .assistant_todos.json "/todo list"
```

Use environment variable instead of passing the flag each time:

```bash
export ASSISTANTS_STATE_FILE=.assistant_todos.json
python3 -m src.assistant_echo "/todo buy milk"
python3 -m src.assistant_echo "/todo list"
```

Disable persistence for one-off runs:

```bash
python3 -m src.assistant_echo --state-file "" "/todo list"
```

Run tests:

```bash
python3 -m unittest discover -s tests -p "test_*.py"
make coverage
```

Makefile shortcuts:

```bash
make run MSG="hello"
make run-persistent MSG="/todo list" STATE_FILE=.assistant_todos.json
make test
make coverage
make health
make version
make ingest-money-status
PGPASSWORD='***' GOOGLE_SERVICE_ACCOUNT_FILE=.secrets/bank-drive-sa.json \
GOOGLE_DRIVE_FOLDER_ID='your-folder-id' make ingest-money
```

Bank ETL target defaults for `make ingest-money`:

- `MONEY_PGHOST=127.0.0.1`
- `MONEY_PGPORT=5434`
- `MONEY_PGDATABASE=money`
- `MONEY_PGUSER=money`
- `MONEY_BANK_OUTPUT_DIR=./artifacts`
- `MONEY_INCLUDE_NAME_REGEX=^(stancard_2503\.csv|RJK_All25\.csv)$`
- `MONEY_EXCLUDE_NAME_REGEX=^statement-`

This default filter excludes `statement-...` files and keeps only
`stancard_2503.csv` and `RJK_All25.csv`.

To override filtering for a run:

```bash
MONEY_INCLUDE_NAME_REGEX='.*\.(csv|pdf)$' MONEY_EXCLUDE_NAME_REGEX='' make ingest-money
```

Required environment variables:

- `GOOGLE_SERVICE_ACCOUNT_FILE`
- `GOOGLE_DRIVE_FOLDER_ID`
- `PGPASSWORD`

## Milestone v0.1 (Initial Target)

1. Define a single assistant use case and expected inputs/outputs.
2. Implement a first workflow under `src/`.
3. Add baseline tests for the workflow.
4. Document usage and known limitations.

## Bank ETL Agent Blueprint

For a concrete implementation plan for Google Drive statement ingestion and
PostgreSQL loading, see:

- `docs/bank-agent-implementation.md`
- `sql/bank_ingestion_schema.sql`
- `src/bank_statement_agent.py`

## License

This project is licensed under the terms in `LICENSE`.

## Changelog

Release history is tracked in `CHANGELOG.md`.
