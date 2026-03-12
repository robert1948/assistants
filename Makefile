PYTHON ?= python3

.PHONY: run test help

help:
	@echo "Targets:"
	@echo "  make run MSG='hello'   - run assistant with a message"
	@echo "  make test              - run unit tests"

run:
	$(PYTHON) -m src.assistant_echo "$(MSG)"

test:
	$(PYTHON) -m unittest discover -s tests -p "test_*.py"
