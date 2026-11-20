# Muhammad Afnan | 23pwbcs0999 | 20 November 2026

import unittest

import pandas as pd

from src.validation import expected_columns, validate_raw_input


class RawValidationTests(unittest.TestCase):
    def setUp(self):
        self.sample = pd.DataFrame({name: [None, None] for name in sorted(expected_columns)})
        self.sample["Inspection ID"] = [101, 102]
        self.sample["Inspection Date"] = ["01/02/2023", "12/31/2024"]

    def test_valid_input_returns_parsed_dates(self):
        dates = validate_raw_input(self.sample)
        self.assertEqual(dates.dt.strftime("%Y-%m-%d").tolist(), ["2023-01-02", "2024-12-31"])

    def test_missing_column_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "expected schema"):
            validate_raw_input(self.sample.drop(columns="Risk"))

    def test_empty_input_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "no rows"):
            validate_raw_input(self.sample.iloc[:0])

    def test_duplicate_id_is_rejected(self):
        self.sample.loc[1, "Inspection ID"] = 101
        with self.assertRaisesRegex(ValueError, "present and unique"):
            validate_raw_input(self.sample)

    def test_missing_id_is_rejected(self):
        self.sample["Inspection ID"] = pd.Series([101, pd.NA], dtype="Int64")
        with self.assertRaisesRegex(ValueError, "present and unique"):
            validate_raw_input(self.sample)

    def test_text_ids_are_rejected(self):
        self.sample["Inspection ID"] = ["ABC", "DEF"]
        with self.assertRaisesRegex(ValueError, "must be integers"):
            validate_raw_input(self.sample)

    def test_invalid_date_is_rejected(self):
        self.sample.loc[0, "Inspection Date"] = "invalid-date"
        with self.assertRaisesRegex(ValueError, "missing or invalid"):
            validate_raw_input(self.sample)
