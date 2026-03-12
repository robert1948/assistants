# Bank Statement Agent Implementation Blueprint

This document describes how to build an AI-assisted ETL agent that:

1. Retrieves bank statements from Google Drive.
2. Merges them into one normalized CSV.
3. Loads that data into a target table in local PostgreSQL.

## 1. Scope and assumptions

- Statements are stored in one Drive folder (or a small set of folders).
- Supported formats for first release: CSV and XLSX.
- PDF support is optional and should be added as a separate parser module.
- Data is loaded to a local PostgreSQL instance.

## 2. Security baseline

- Use a dedicated Google OAuth app or service account with minimum Drive scope.
- Use a dedicated PostgreSQL user with only required schema/table permissions.
- Store credentials in environment variables, not source code.
- Exclude local token/state files from git.

Suggested environment variables:

- `GOOGLE_DRIVE_FOLDER_ID`
- `GOOGLE_CLIENT_SECRET_PATH` (for OAuth local flow)
- `GOOGLE_TOKEN_PATH` (persisted auth token)
- `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`
- `BANK_ETL_OUTPUT_DIR`

Suggested Python packages:

- `google-api-python-client`
- `google-auth`
- `psycopg[binary]`
- `openpyxl` (only if ingesting `.xlsx` statements)

## 3. Workflow

1. Discover candidate files from Google Drive folder.
2. Filter files by name/mime type/date.
3. Skip already-processed files using ingestion history table.
4. Download files to a temporary run directory.
5. Parse and normalize records to canonical schema.
6. Merge all records into one CSV file.
7. Load merged CSV to staging table.
8. Upsert from staging to target table.
9. Record file and run metadata in audit/history tables.

## 4. Suggested canonical transaction schema

- `statement_date` (date)
- `transaction_date` (date)
- `description` (text)
- `amount` (numeric)
- `currency` (text)
- `account_last4` (text)
- `bank_name` (text)
- `source_file_id` (text)
- `source_file_name` (text)
- `source_row_hash` (text)
- `ingested_at` (timestamp)

`source_row_hash` is used to avoid duplicates across re-runs.

## 5. Idempotency strategy

- Track processed Drive file IDs in `bank_ingestion_file_history`.
- Track row-level uniqueness with `source_row_hash` unique constraint.
- Use `INSERT ... ON CONFLICT` for final table merge.

## 6. Error handling strategy

- Per-file try/catch so one bad statement does not fail entire run.
- Retry transient Drive/API errors with exponential backoff.
- Abort DB merge when schema validation fails.
- Always write a run record with status `success` or `failed`.

## 7. Rollout phases

- Phase 1: CSV/XLSX parsers + local manual runs.
- Phase 2: Add scheduling (cron/systemd timer).
- Phase 3: Add PDF parser and quality checks.
- Phase 4: Add notifications and dashboard metrics.

## 8. Minimum acceptance checks

- End-to-end run creates merged CSV.
- Staging load row count equals merged CSV row count.
- Upsert count matches expected new/updated records.
- Re-running without new files produces zero new rows.
