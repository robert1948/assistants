"""Bank statement ETL agent skeleton.

This module provides a practical orchestration template for:
1) downloading statements from Google Drive,
2) normalizing and merging records,
3) loading records to PostgreSQL.

Note: external integrations are intentionally left as stubs with clear TODOs.
"""

from __future__ import annotations

import csv
import hashlib
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class DriveFile:
    file_id: str
    name: str
    mime_type: str
    modified_time: str | None = None


@dataclass
class NormalizedTransaction:
    statement_date: str | None
    transaction_date: str
    description: str
    amount: str
    currency: str | None
    account_last4: str | None
    bank_name: str | None
    source_file_id: str
    source_file_name: str
    source_row_hash: str
    ingested_at: str


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def discover_drive_files(folder_id: str) -> list[DriveFile]:
    """Discover candidate statement files from Google Drive.

    TODO: Implement with Google Drive API.
    Filters should include mime type and optional naming/date rules.
    """
    _ = folder_id
    return []


def download_drive_file(file: DriveFile, target_dir: Path) -> Path:
    """Download a Drive file to target_dir and return local path.

    TODO: Implement with Google Drive API media download.
    """
    target_path = target_dir / file.name
    target_path.touch()
    return target_path


def parse_statement_file(local_path: Path, file: DriveFile) -> list[dict[str, Any]]:
    """Parse a statement file into raw row dictionaries.

    TODO: Implement format-specific parsers (CSV/XLSX/PDF).
    """
    _ = local_path
    _ = file
    return []


def normalize_rows(raw_rows: list[dict[str, Any]], file: DriveFile) -> list[NormalizedTransaction]:
    """Normalize raw rows into canonical transaction records."""
    normalized: list[NormalizedTransaction] = []
    now_iso = datetime.now(UTC).isoformat()

    for row in raw_rows:
        tx_date = str(row.get("transaction_date", "")).strip()
        desc = str(row.get("description", "")).strip()
        amt = str(row.get("amount", "")).strip()
        if not tx_date or not desc or not amt:
            continue

        raw_fingerprint = f"{tx_date}|{desc}|{amt}|{file.file_id}|{file.name}"
        row_hash = hashlib.sha256(raw_fingerprint.encode("utf-8")).hexdigest()

        normalized.append(
            NormalizedTransaction(
                statement_date=(str(row.get("statement_date", "")).strip() or None),
                transaction_date=tx_date,
                description=desc,
                amount=amt,
                currency=(str(row.get("currency", "")).strip() or None),
                account_last4=(str(row.get("account_last4", "")).strip() or None),
                bank_name=(str(row.get("bank_name", "")).strip() or None),
                source_file_id=file.file_id,
                source_file_name=file.name,
                source_row_hash=row_hash,
                ingested_at=now_iso,
            )
        )

    return normalized


def write_merged_csv(records: list[NormalizedTransaction], output_dir: Path) -> Path:
    """Write normalized records to one CSV and return its path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out_path = output_dir / f"bank_transactions_merged_{ts}.csv"

    fieldnames = [
        "statement_date",
        "transaction_date",
        "description",
        "amount",
        "currency",
        "account_last4",
        "bank_name",
        "source_file_id",
        "source_file_name",
        "source_row_hash",
        "ingested_at",
    ]

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(record.__dict__)

    return out_path


def load_csv_to_postgres(csv_path: Path) -> int:
    """Load merged CSV into PostgreSQL staging and upsert into final table.

    TODO: Implement with psycopg or SQLAlchemy.
    Recommended sequence:
    1) BEGIN transaction
    2) TRUNCATE staging
    3) COPY CSV into staging
    4) INSERT .. ON CONFLICT into final table
    5) COMMIT

    Return number of rows upserted.
    """
    _ = csv_path
    return 0


def run_agent() -> None:
    folder_id = _required_env("GOOGLE_DRIVE_FOLDER_ID")
    output_dir = Path(os.getenv("BANK_ETL_OUTPUT_DIR", "./artifacts"))
    temp_dir = output_dir / "tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    drive_files = discover_drive_files(folder_id)

    all_records: list[NormalizedTransaction] = []
    for file in drive_files:
        local_file = download_drive_file(file, temp_dir)
        raw_rows = parse_statement_file(local_file, file)
        all_records.extend(normalize_rows(raw_rows, file))

    merged_csv = write_merged_csv(all_records, output_dir)
    rows_loaded = load_csv_to_postgres(merged_csv)

    print(
        f"Run completed. files={len(drive_files)} rows={len(all_records)} "
        f"loaded={rows_loaded} csv={merged_csv}"
    )


if __name__ == "__main__":
    run_agent()
