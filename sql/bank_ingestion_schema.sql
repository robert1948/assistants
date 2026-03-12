-- PostgreSQL schema for bank statement ingestion agent.
-- Adjust schema name and table names as needed.

CREATE SCHEMA IF NOT EXISTS bank_ingestion;

CREATE TABLE IF NOT EXISTS bank_ingestion.bank_ingestion_runs (
    run_id BIGSERIAL PRIMARY KEY,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    status TEXT NOT NULL,
    files_discovered INTEGER NOT NULL DEFAULT 0,
    files_processed INTEGER NOT NULL DEFAULT 0,
    rows_normalized INTEGER NOT NULL DEFAULT 0,
    rows_loaded_staging INTEGER NOT NULL DEFAULT 0,
    rows_upserted_final INTEGER NOT NULL DEFAULT 0,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS bank_ingestion.bank_ingestion_file_history (
    file_id TEXT PRIMARY KEY,
    file_name TEXT NOT NULL,
    mime_type TEXT,
    modified_time TIMESTAMPTZ,
    checksum TEXT,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    run_id BIGINT REFERENCES bank_ingestion.bank_ingestion_runs(run_id)
);

CREATE TABLE IF NOT EXISTS bank_ingestion.bank_transactions_staging (
    statement_date DATE,
    transaction_date DATE NOT NULL,
    description TEXT NOT NULL,
    amount NUMERIC(18, 2) NOT NULL,
    currency TEXT,
    account_last4 TEXT,
    bank_name TEXT,
    source_file_id TEXT NOT NULL,
    source_file_name TEXT NOT NULL,
    source_row_hash TEXT NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bank_ingestion.bank_transactions (
    transaction_id BIGSERIAL PRIMARY KEY,
    statement_date DATE,
    transaction_date DATE NOT NULL,
    description TEXT NOT NULL,
    amount NUMERIC(18, 2) NOT NULL,
    currency TEXT,
    account_last4 TEXT,
    bank_name TEXT,
    source_file_id TEXT NOT NULL,
    source_file_name TEXT NOT NULL,
    source_row_hash TEXT NOT NULL UNIQUE,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bank_transactions_date
    ON bank_ingestion.bank_transactions(transaction_date);

CREATE INDEX IF NOT EXISTS idx_bank_transactions_account
    ON bank_ingestion.bank_transactions(account_last4);

-- Example upsert from staging to final.
-- Run inside a transaction after loading staging.
--
-- INSERT INTO bank_ingestion.bank_transactions (
--     statement_date,
--     transaction_date,
--     description,
--     amount,
--     currency,
--     account_last4,
--     bank_name,
--     source_file_id,
--     source_file_name,
--     source_row_hash,
--     ingested_at
-- )
-- SELECT
--     statement_date,
--     transaction_date,
--     description,
--     amount,
--     currency,
--     account_last4,
--     bank_name,
--     source_file_id,
--     source_file_name,
--     source_row_hash,
--     ingested_at
-- FROM bank_ingestion.bank_transactions_staging
-- ON CONFLICT (source_row_hash) DO NOTHING;
