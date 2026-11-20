# Muhammad Afnan | 23pwbcs0999 | 20 November 2026

import unittest

import pandas as pd

from src.cleaning import clean_category_labels, invalid_coordinates


class CleaningTests(unittest.TestCase):
    def test_trims_labels_and_retains_missing_values(self):
        labels = pd.Series(["  Canvass ", "   ", pd.NA, "All"], dtype="string")
        expected = pd.Series(["Canvass", pd.NA, pd.NA, "All"], dtype="string")
        pd.testing.assert_series_equal(clean_category_labels(labels), expected)

    def test_flags_incomplete_and_out_of_range_pairs(self):
        latitudes = pd.Series([41.88, None, 95.0, 41.88, -90.0, 41.88])
        longitudes = pd.Series([-87.63, None, -87.63, None, 180.0, 181.0])
        self.assertEqual(
            invalid_coordinates(latitudes, longitudes).tolist(),
            [False, False, True, True, False, True],
        )
