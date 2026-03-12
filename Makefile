PYTHON ?= python3
STATE_FILE ?= .assistant_todos.json
TEST_PATTERN ?= test_*.py

.PHONY: run run-persistent test coverage health version help

help:
	@echo "Targets:"
	@echo "  make run MSG='hello'   - run assistant with a message"
	@echo "  make run-persistent MSG='/todo list' STATE_FILE=.assistant_todos.json"
	@echo "                           run assistant with persisted todo state"
	@echo "  make test              - run unit tests"
	@echo "  make coverage          - run tests with coverage report"
	@echo "  make health            - run assistant health check"
	@echo "  make version           - print assistant version"

run:
	$(PYTHON) -m src.assistant_echo "$(MSG)"

run-persistent:
	$(PYTHON) -m src.assistant_echo --state-file "$(STATE_FILE)" "$(MSG)"

test:
	$(PYTHON) -m unittest discover -s tests -p "$(TEST_PATTERN)"

coverage:
	$(PYTHON) -m coverage run -m unittest discover -s tests -p "$(TEST_PATTERN)"
	$(PYTHON) -m coverage report -m

health:
	$(PYTHON) -m src.assistant_echo --health

version:
	$(PYTHON) -m src.assistant_echo --version
