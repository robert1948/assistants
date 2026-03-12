PYTHON ?= python3
STATE_FILE ?= .assistant_todos.json

.PHONY: run run-persistent test health version help

help:
	@echo "Targets:"
	@echo "  make run MSG='hello'   - run assistant with a message"
	@echo "  make run-persistent MSG='/todo list' STATE_FILE=.assistant_todos.json"
	@echo "                           run assistant with persisted todo state"
	@echo "  make test              - run unit tests"
	@echo "  make health            - run assistant health check"
	@echo "  make version           - print assistant version"

run:
	$(PYTHON) -m src.assistant_echo "$(MSG)"

run-persistent:
	$(PYTHON) -m src.assistant_echo --state-file "$(STATE_FILE)" "$(MSG)"

test:
	$(PYTHON) -m unittest discover -s tests -p "test_*.py"

health:
	$(PYTHON) -m src.assistant_echo --health

version:
	$(PYTHON) -m src.assistant_echo --version
