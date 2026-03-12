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
```

Run tests:

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

## Milestone v0.1 (Initial Target)

1. Define a single assistant use case and expected inputs/outputs.
2. Implement a first workflow under `src/`.
3. Add baseline tests for the workflow.
4. Document usage and known limitations.

## License

This project is licensed under the terms in `LICENSE`.
