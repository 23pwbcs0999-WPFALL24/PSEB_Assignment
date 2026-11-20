# Muhammad Afnan | 23pwbcs0999 | 20 November 2026

import pandas as pd

expected_columns = {
    "Inspection ID", "DBA Name", "AKA Name", "License #",
    "Facility Type", "Risk", "Address", "City", "State", "Zip",
    "Inspection Date", "Inspection Type", "Results", "Violations",
    "Latitude", "Longitude", "Location",
}


def validate_raw_input(frame):
    """Check the CSV columns, inspection IDs, and dates."""
    if frame.empty:
        raise ValueError("The input contains no rows.")

    if not frame.columns.is_unique or set(frame.columns) != expected_columns:
        raise ValueError("The input columns differ from the expected schema.")

    ids = frame["Inspection ID"]
    if ids.isna().any() or ids.duplicated().any():
        raise ValueError("Inspection IDs must be present and unique.")

    if not pd.api.types.is_integer_dtype(ids.dtype):
        raise ValueError("Inspection IDs must be integers.")

    dates = pd.to_datetime(
        frame["Inspection Date"], format="%m/%d/%Y", errors="coerce"
    )
    if dates.isna().any():
        raise ValueError("At least one inspection date is missing or invalid.")

    return dates
