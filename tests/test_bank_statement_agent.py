import csv
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from src.bank_statement_agent import (
    DriveFile,
    _parse_legacy_bank_csv,
    _parse_pdf_rows_from_text,
    get_processed_file_ids,
    normalize_rows,
    parse_statement_file,
    record_processed_files,
    write_merged_csv,
)


class BankStatementAgentTests(unittest.TestCase):
    def test_parse_csv_statement(self) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "statement.csv"
            path.write_text(
                "transaction_date,description,amount,currency\n"
                "2026-03-01,Coffee,-4.50,USD\n",
                encoding="utf-8",
            )
            drive_file = DriveFile("f1", "statement.csv", "text/csv")
            rows = parse_statement_file(path, drive_file)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["description"], "Coffee")

    def test_parse_google_sheet_exported_csv(self) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "statement.csv"
            path.write_text(
                "transaction_date,description,amount\n" "2026-03-02,Tea,-2.25\n",
                encoding="utf-8",
            )
            drive_file = DriveFile(
                "f2", "statement", "application/vnd.google-apps.spreadsheet"
            )
            rows = parse_statement_file(path, drive_file)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["description"], "Tea")

    def test_normalize_rows_skips_incomplete(self) -> None:
        drive_file = DriveFile("f1", "statement.csv", "text/csv")
        raw_rows = [
            {
                "transaction_date": "2026-03-01",
                "description": "Coffee",
                "amount": "-4.50",
                "currency": "USD",
            },
            {
                "transaction_date": "",
                "description": "Missing date",
                "amount": "1.00",
            },
        ]

        normalized = normalize_rows(raw_rows, drive_file)
        self.assertEqual(len(normalized), 1)
        self.assertEqual(normalized[0].description, "Coffee")
        self.assertEqual(normalized[0].source_file_id, "f1")

    def test_write_merged_csv(self) -> None:
        drive_file = DriveFile("f1", "statement.csv", "text/csv")
        normalized = normalize_rows(
            [
                {
                    "statement_date": "2026-03-01",
                    "transaction_date": "2026-03-01",
                    "description": "Coffee",
                    "amount": "-4.50",
                    "currency": "USD",
                }
            ],
            drive_file,
        )

        with TemporaryDirectory() as tmpdir:
            output = write_merged_csv(normalized, Path(tmpdir))
            self.assertTrue(output.exists())

            with output.open("r", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["description"], "Coffee")

    def test_parse_pdf_rows_from_text(self) -> None:
        text = (
            "2026-03-01 COFFEE SHOP -4.50\n"
            "not a valid line\n"
            "03/02/2026 SALARY 1500.00\n"
            "14 Jul 2024 ***0522 POS Purchase CLICKS SANTYGER PHARM Western Cape  - R2 311.09\n"
        )
        rows = _parse_pdf_rows_from_text(text)

        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["transaction_date"], "2026-03-01")
        self.assertEqual(rows[0]["description"], "COFFEE SHOP")
        self.assertEqual(rows[0]["amount"], "-4.50")

    def test_parse_legacy_bank_csv(self) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "legacy.csv"
            path.write_text(
                "0,410,BRANCH,0,,TYGERMANOR,0,0\n"
                "HIST,20210526,,2702.5,CATS THIRD PARTY PAYMENT,CHEPZA1020001691008611118,134,0\n"
                "HIST,20210528,,-207,IMMEDIATE PAYMENT,18128695 THE COURIER GUY,1714,0\n",
                encoding="utf-8",
            )
            rows = _parse_legacy_bank_csv(path)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["transaction_date"], "2021-05-26")
        self.assertEqual(rows[0]["amount"], "2702.50")
        self.assertIn("CATS THIRD PARTY PAYMENT", rows[0]["description"])

    @patch("src.bank_statement_agent._import_psycopg")
    def test_get_processed_file_ids(self, mock_import_psycopg) -> None:
        mock_connect = mock_import_psycopg.return_value.connect
        mock_conn = mock_connect.return_value.__enter__.return_value
        mock_cur = mock_conn.cursor.return_value.__enter__.return_value
        mock_cur.fetchall.return_value = [("file1",), ("file2",)]

        ids = get_processed_file_ids()

        self.assertEqual(ids, {"file1", "file2"})

    @patch("src.bank_statement_agent._import_psycopg")
    def test_record_processed_files(self, mock_import_psycopg) -> None:
        files = [
            DriveFile("f1", "a.csv", "text/csv"),
            DriveFile("f2", "b.pdf", "application/pdf"),
        ]
        mock_connect = mock_import_psycopg.return_value.connect
        mock_conn = mock_connect.return_value.__enter__.return_value
        mock_cur = mock_conn.cursor.return_value.__enter__.return_value

        record_processed_files(files)

        self.assertEqual(mock_cur.execute.call_count, 2)
        mock_conn.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
