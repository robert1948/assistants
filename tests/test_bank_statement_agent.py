import csv
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.bank_statement_agent import (
    DriveFile,
    normalize_rows,
    parse_statement_file,
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


if __name__ == "__main__":
    unittest.main()
