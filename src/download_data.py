# Muhammad Afnan | 23pwbcs0999 | 20 November 2026

"""Fetch the current City of Chicago CSV without replacing an existing snapshot."""

import argparse
import csv
from pathlib import Path
from shutil import copyfileobj
from tempfile import TemporaryDirectory
from urllib.request import urlopen

from src.validation import expected_columns

SOURCE_URL = "https://data.cityofchicago.org/api/v3/views/4ijn-s7e5/export.csv?accessType=DOWNLOAD"
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main():
    """Download the live export and check its header before publishing it locally."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "data/raw/Food_Inspections_live.csv")
    destination = parser.parse_args().output

    if destination.exists():
        parser.error(f"File already exists: {destination}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with TemporaryDirectory(dir=destination.parent) as temp_dir:
            temporary_csv = Path(temp_dir) / "download.csv"
            with urlopen(SOURCE_URL, timeout=120) as response, temporary_csv.open("wb") as file:
                copyfileobj(response, file)
            with temporary_csv.open(encoding="utf-8-sig", newline="") as file:
                columns = next(csv.reader(file), [])
            if len(columns) != len(expected_columns) or set(columns) != expected_columns:
                raise ValueError("The download did not contain the expected CSV columns.")
            destination.hardlink_to(temporary_csv)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Download failed: {error}\n")

    print(f"Saved live data to {destination}")


if __name__ == "__main__":
    main()
