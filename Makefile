PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
STATE_FILE ?= .assistant_todos.json
TEST_PATTERN ?= test_*.py
MONEY_PGHOST ?= 127.0.0.1
MONEY_PGPORT ?= 5434
MONEY_PGDATABASE ?= money
MONEY_PGUSER ?= money
MONEY_BANK_OUTPUT_DIR ?= ./artifacts

.PHONY: run run-persistent test coverage health version help check-ingest-env ingest-money ingest-money-status

help:
	@echo "Targets:"
	@echo "  make run MSG='hello'   - run assistant with a message"
	@echo "  make run-persistent MSG='/todo list' STATE_FILE=.assistant_todos.json"
	@echo "                           run assistant with persisted todo state"
	@echo "  make test              - run unit tests"
	@echo "  make coverage          - run tests with coverage report"
	@echo "  make health            - run assistant health check"
	@echo "  make version           - print assistant version"
	@echo "  make ingest-money      - run bank ETL into Money DB via localhost:5434"
	@echo "  make ingest-money-status"
	@echo "                         show row counts for Money DB ingestion tables"

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

check-ingest-env:
	@test -n "$(GOOGLE_SERVICE_ACCOUNT_FILE)" || (echo "Missing GOOGLE_SERVICE_ACCOUNT_FILE" && exit 1)
	@test -n "$(GOOGLE_DRIVE_FOLDER_ID)" || (echo "Missing GOOGLE_DRIVE_FOLDER_ID" && exit 1)
	@test -n "$(PGPASSWORD)" || (echo "Missing PGPASSWORD" && exit 1)

ingest-money: check-ingest-env
	GOOGLE_SERVICE_ACCOUNT_FILE="$(GOOGLE_SERVICE_ACCOUNT_FILE)" \
	GOOGLE_DRIVE_FOLDER_ID="$(GOOGLE_DRIVE_FOLDER_ID)" \
	BANK_ETL_OUTPUT_DIR="$(MONEY_BANK_OUTPUT_DIR)" \
	PGHOST="$(MONEY_PGHOST)" \
	PGPORT="$(MONEY_PGPORT)" \
	PGDATABASE="$(MONEY_PGDATABASE)" \
	PGUSER="$(MONEY_PGUSER)" \
	PGPASSWORD="$(PGPASSWORD)" \
	$(PYTHON) -m src.bank_statement_agent

ingest-money-status: check-ingest-env
	PGPASSWORD="$(PGPASSWORD)" psql "host=$(MONEY_PGHOST) port=$(MONEY_PGPORT) dbname=$(MONEY_PGDATABASE) user=$(MONEY_PGUSER) sslmode=disable" \
		-c "select count(*) as history_rows from bank_ingestion.bank_ingestion_file_history;" \
		-c "select count(*) as staging_rows from bank_ingestion.bank_transactions_staging;" \
		-c "select count(*) as final_rows from bank_ingestion.bank_transactions;"
