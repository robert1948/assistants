"""Bank statement ETL agent implementation template.

This module provides a practical orchestration template for:
1) downloading statements from Google Drive,
2) normalizing and merging records,
3) loading records to PostgreSQL.

Google Drive and PostgreSQL integrations are implemented with optional
dependencies and explicit environment-variable configuration.
"""

from __future__ import annotations

import csv
import hashlib
import os
import re
from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SUPPORTED_FILE_MIME_TYPES = {
    "text/csv",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.google-apps.spreadsheet",
    "application/pdf",
}

FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"

DATE_TOKEN_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})$")
AMOUNT_TOKEN_RE = re.compile(r"^[+-]?\d[\d,]*\.?\d{0,2}$")
PDF_TX_LINE_RE = re.compile(
    r"^(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})\s+(.+?)\s+-\s+R\s*([\d\s,]+\.\d{2})$"
)


def _import_psycopg() -> Any:
    try:
        import psycopg
    except ImportError as exc:
        raise RuntimeError(
            "PostgreSQL dependency missing. Install: psycopg[binary]"
        ) from exc
    return psycopg


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


def _build_drive_service() -> Any:
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError(
            "Google Drive dependencies missing. Install: "
            "google-api-python-client google-auth"
        ) from exc

    creds_path = _required_env("GOOGLE_SERVICE_ACCOUNT_FILE")
    scopes = ["https://www.googleapis.com/auth/drive.readonly"]
    credentials = service_account.Credentials.from_service_account_file(
        creds_path, scopes=scopes
    )
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


def discover_drive_files(folder_id: str) -> list[DriveFile]:
    """Discover candidate statement files from Google Drive recursively."""
    service = _build_drive_service()

    fields = "files(id, name, mimeType, modifiedTime), nextPageToken"

    drive_files: list[DriveFile] = []
    queue: deque[str] = deque([folder_id])

    while queue:
        current_folder = queue.popleft()
        query = f"'{current_folder}' in parents and trashed = false"

        page_token: str | None = None
        while True:
            response = (
                service.files()
                .list(
                    q=query,
                    fields=fields,
                    pageToken=page_token,
                    pageSize=1000,
                    includeItemsFromAllDrives=False,
                    supportsAllDrives=False,
                )
                .execute()
            )

            for f in response.get("files", []):
                mime_type = f.get("mimeType", "")
                if mime_type == FOLDER_MIME_TYPE:
                    queue.append(f["id"])
                    continue
                if mime_type not in SUPPORTED_FILE_MIME_TYPES:
                    continue
                drive_files.append(
                    DriveFile(
                        file_id=f["id"],
                        name=f["name"],
                        mime_type=mime_type,
                        modified_time=f.get("modifiedTime"),
                    )
                )

            page_token = response.get("nextPageToken")
            if not page_token:
                break

    return drive_files


def download_drive_file(file: DriveFile, target_dir: Path) -> Path:
    """Download a Drive file to target_dir and return local path."""
    try:
        from googleapiclient.http import MediaIoBaseDownload
    except ImportError as exc:
        raise RuntimeError(
            "Google Drive dependencies missing. Install: "
            "google-api-python-client google-auth"
        ) from exc

    target_dir.mkdir(parents=True, exist_ok=True)
    service = _build_drive_service()

    # Google Sheets require export instead of media download.
    if file.mime_type == "application/vnd.google-apps.spreadsheet":
        output_name = (
            file.name if file.name.lower().endswith(".csv") else f"{file.name}.csv"
        )
        target_path = target_dir / output_name
        request = service.files().export_media(fileId=file.file_id, mimeType="text/csv")
    else:
        target_path = target_dir / file.name
        request = service.files().get_media(fileId=file.file_id)

    with target_path.open("wb") as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

    return target_path


def parse_statement_file(local_path: Path, file: DriveFile) -> list[dict[str, Any]]:
    """Parse a statement file into raw row dictionaries."""
    suffix = local_path.suffix.lower()

    if suffix == ".csv" or file.mime_type in {"text/csv", "application/vnd.ms-excel"}:
        with local_path.open("r", encoding="utf-8-sig", newline="") as f:
            dict_rows = [dict(row) for row in csv.DictReader(f)]

        # Legacy bank CSVs may have no header and fixed-position columns.
        if not dict_rows or _looks_like_headerless_csv(dict_rows[0]):
            return _parse_legacy_bank_csv(local_path)

        return dict_rows

    if file.mime_type == "application/vnd.google-apps.spreadsheet" and suffix == ".csv":
        with local_path.open("r", encoding="utf-8-sig", newline="") as f:
            return [dict(row) for row in csv.DictReader(f)]

    if suffix == ".xlsx" or file.mime_type == (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ):
        try:
            from openpyxl import load_workbook
        except ImportError as exc:
            raise RuntimeError(
                "XLSX support requires openpyxl. Install: openpyxl"
            ) from exc

        wb = load_workbook(local_path, read_only=True, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return []
        headers = [str(cell).strip() if cell is not None else "" for cell in rows[0]]
        parsed: list[dict[str, Any]] = []
        for row in rows[1:]:
            parsed.append(
                {
                    headers[idx]: ("" if value is None else str(value).strip())
                    for idx, value in enumerate(row)
                    if idx < len(headers) and headers[idx]
                }
            )
        return parsed

    if suffix == ".pdf" or file.mime_type == "application/pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("PDF support requires pypdf. Install: pypdf") from exc

        reader = PdfReader(str(local_path))
        text_chunks: list[str] = []
        for page in reader.pages:
            text_chunks.append(page.extract_text() or "")
        return _parse_pdf_rows_from_text("\n".join(text_chunks))

    raise ValueError(f"Unsupported statement format: {local_path.name}")


def _parse_pdf_rows_from_text(text: str) -> list[dict[str, Any]]:
    """Heuristic parser for PDF text rows: <date> <description> <amount>."""
    parsed: list[dict[str, Any]] = []
    for raw_line in text.splitlines():
        line = " ".join(raw_line.strip().split())
        if not line:
            continue

        matched = PDF_TX_LINE_RE.match(line)
        if matched:
            date_token, details_token, amount_token = matched.groups()
            tx_date = _normalize_date(date_token)
            description = details_token.strip()
            amount = _normalize_amount(amount_token)
            if tx_date and description and amount:
                parsed.append(
                    {
                        "transaction_date": tx_date,
                        "description": description,
                        "amount": amount,
                    }
                )
            continue

        tokens = line.split(" ")
        if len(tokens) < 3:
            continue
        if not DATE_TOKEN_RE.match(tokens[0]):
            continue
        if not AMOUNT_TOKEN_RE.match(tokens[-1]):
            continue

        amount = tokens[-1].replace(",", "")
        description = " ".join(tokens[1:-1]).strip()
        if not description:
            continue

        parsed.append(
            {
                "transaction_date": tokens[0],
                "description": description,
                "amount": amount,
            }
        )
    return parsed


def _looks_like_headerless_csv(first_row: dict[str, Any]) -> bool:
    keys = {k.strip() for k in first_row.keys() if k is not None}
    expected = {"transaction_date", "description", "amount"}
    return not expected.issubset(keys)


def _parse_legacy_bank_csv(local_path: Path) -> list[dict[str, Any]]:
    parsed: list[dict[str, Any]] = []
    with local_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 5:
                continue
            if row[0].strip().upper() != "HIST":
                continue

            tx_date = _normalize_date(row[1].strip())
            amount = _normalize_amount(row[3].strip())
            description = row[4].strip()
            counterparty = row[5].strip() if len(row) > 5 else ""

            if not tx_date or not amount or not description:
                continue

            if counterparty:
                description = f"{description} | {counterparty}"

            parsed.append(
                {
                    "transaction_date": tx_date,
                    "description": description,
                    "amount": amount,
                }
            )

    return parsed


def _normalize_date(value: str) -> str | None:
    value = value.strip()
    if not value:
        return None

    for fmt in ("%Y-%m-%d", "%Y%m%d", "%d/%m/%Y", "%d %b %Y"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _normalize_amount(value: str) -> str | None:
    value = value.strip()
    if not value:
        return None
    cleaned = value.replace("R", "").replace(" ", "").replace(",", "")
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = f"-{cleaned[1:-1]}"
    if not cleaned:
        return None
    try:
        return f"{float(cleaned):.2f}"
    except ValueError:
        return None


def normalize_rows(
    raw_rows: list[dict[str, Any]], file: DriveFile
) -> list[NormalizedTransaction]:
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

    Return number of rows upserted.
    """
    psycopg = _import_psycopg()

    host = os.getenv("PGHOST", "localhost")
    port = os.getenv("PGPORT", "5432")
    dbname = _required_env("PGDATABASE")
    user = _required_env("PGUSER")
    password = _required_env("PGPASSWORD")

    copy_columns = (
        "statement_date, transaction_date, description, amount, currency, "
        "account_last4, bank_name, source_file_id, source_file_name, "
        "source_row_hash, ingested_at"
    )

    conninfo = (
        f"host={host} port={port} dbname={dbname} user={user} password={password}"
    )

    with psycopg.connect(conninfo) as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE bank_ingestion.bank_transactions_staging")

            with csv_path.open("r", encoding="utf-8") as csv_f:
                with cur.copy(
                    "COPY bank_ingestion.bank_transactions_staging "
                    f"({copy_columns}) FROM STDIN WITH (FORMAT csv, HEADER true)"
                ) as copy:
                    while chunk := csv_f.read(1024 * 1024):
                        copy.write(chunk)

            cur.execute(
                "INSERT INTO bank_ingestion.bank_transactions ("
                "statement_date, transaction_date, description, amount, currency, "
                "account_last4, bank_name, source_file_id, source_file_name, "
                "source_row_hash, ingested_at"
                ") "
                "SELECT "
                "statement_date, transaction_date, description, amount, currency, "
                "account_last4, bank_name, source_file_id, source_file_name, "
                "source_row_hash, ingested_at "
                "FROM bank_ingestion.bank_transactions_staging "
                "ON CONFLICT (source_row_hash) DO NOTHING"
            )
            rows_upserted = cur.rowcount
        conn.commit()

    return max(rows_upserted, 0)


def _build_pg_conninfo() -> str:
    host = os.getenv("PGHOST", "localhost")
    port = os.getenv("PGPORT", "5432")
    dbname = _required_env("PGDATABASE")
    user = _required_env("PGUSER")
    password = _required_env("PGPASSWORD")
    return f"host={host} port={port} dbname={dbname} user={user} password={password}"


def get_processed_file_ids() -> set[str]:
    """Return Drive file IDs already recorded in ingestion history."""
    psycopg = _import_psycopg()

    conninfo = _build_pg_conninfo()
    with psycopg.connect(conninfo) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT file_id FROM bank_ingestion.bank_ingestion_file_history"
            )
            rows = cur.fetchall()
    return {str(r[0]) for r in rows}


def record_processed_files(files: list[DriveFile]) -> None:
    """Upsert processed Drive files into ingestion history."""
    if not files:
        return

    psycopg = _import_psycopg()

    conninfo = _build_pg_conninfo()
    with psycopg.connect(conninfo) as conn:
        with conn.cursor() as cur:
            for f in files:
                cur.execute(
                    "INSERT INTO bank_ingestion.bank_ingestion_file_history "
                    "(file_id, file_name, mime_type, modified_time) "
                    "VALUES (%s, %s, %s, %s) "
                    "ON CONFLICT (file_id) DO UPDATE SET "
                    "file_name = EXCLUDED.file_name, "
                    "mime_type = EXCLUDED.mime_type, "
                    "modified_time = EXCLUDED.modified_time, "
                    "processed_at = NOW()",
                    (f.file_id, f.name, f.mime_type, f.modified_time),
                )
        conn.commit()


def run_agent() -> None:
    folder_id = _required_env("GOOGLE_DRIVE_FOLDER_ID")
    output_dir = Path(os.getenv("BANK_ETL_OUTPUT_DIR", "./artifacts"))
    temp_dir = output_dir / "tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    drive_files = discover_drive_files(folder_id)
    processed_ids = get_processed_file_ids()
    pending_files = [f for f in drive_files if f.file_id not in processed_ids]

    all_records: list[NormalizedTransaction] = []
    processed_now: list[DriveFile] = []
    for file in pending_files:
        local_file = download_drive_file(file, temp_dir)
        raw_rows = parse_statement_file(local_file, file)
        all_records.extend(normalize_rows(raw_rows, file))
        processed_now.append(file)

    merged_csv = write_merged_csv(all_records, output_dir)
    rows_loaded = load_csv_to_postgres(merged_csv)
    record_processed_files(processed_now)

    print(
        f"Run completed. files_discovered={len(drive_files)} "
        f"files_processed={len(pending_files)} files_skipped={len(processed_ids)} "
        f"rows={len(all_records)} loaded={rows_loaded} csv={merged_csv}"
    )


if __name__ == "__main__":
    run_agent()
