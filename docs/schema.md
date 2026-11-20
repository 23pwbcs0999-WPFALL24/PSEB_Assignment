# Chicago Food Inspections Raw Data Schema

The City of Chicago Food Inspections CSV has 318,627 rows and 17 columns. This project profiles the 37,489 rows dated January 2023 through December 2024, inclusive. Each row is one inspection record. A facility may appear in multiple inspections.

Missing counts and pandas-inferred types come from the 37,489-row study window. The project type describes how the cleaning pipeline should interpret each value.

| Raw column | Inferred type | Project type | Meaning, domain, or unit | Missing |
| --- | --- | --- | --- | ---: |
| `Inspection ID` | `int64` | Integer identifier | Identifies an inspection. Check presence and uniqueness. | 0 |
| `DBA Name` | `str` | Text | Business name used in trade. | 0 |
| `AKA Name` | `str` | Text | Alternate name recorded for the establishment. | 38 |
| `License #` | `float64` | Identifier | Establishment licence number. Treat it as an identifier when importing. | 1 |
| `Facility Type` | `str` | Category | Establishment category reported in the source. Profile labels before defining a mapping. | 166 |
| `Risk` | `str` | Category | Source risk designation. The observed labels and counts are listed below. | 7 |
| `Address` | `str` | Text | Street address of the establishment. | 0 |
| `City` | `str` | Text | City recorded in the establishment address. | 24 |
| `State` | `str` | Text | State recorded in the establishment address. | 9 |
| `Zip` | `float64` | Text identifier | Postal code. Use text to preserve leading zeros and check length before standardizing. | 4 |
| `Inspection Date` | `str` | Date | Calendar date of the inspection. The study window uses dates from 2023-01-01 up to, but excluding, 2025-01-01. | 0 |
| `Inspection Type` | `str` | Category | Reason or type of inspection. Observed examples include `Canvass`, `License`, and `Complaint`. | 0 |
| `Results` | `str` | Category | Recorded inspection outcome. The model cohort uses `Fail`, `Pass`, and `Pass w/ Conditions`. | 0 |
| `Violations` | `str` | Text | Violation descriptions recorded at inspection time. A blank has no confirmed interpretation on its own. | 11,717 |
| `Latitude` | `float64` | Decimal number | Latitude in degrees. Valid range −90 to 90. | 126 |
| `Longitude` | `float64` | Decimal number | Longitude in degrees. Valid range −180 to 180. | 126 |
| `Location` | `str` | Coordinate pair | Combined point field. Inspect the raw representation and compare populated values with latitude and longitude. | 126 |

## Observed risk values

| Raw value | Rows |
| --- | ---: |
| `Risk 1 (High)` | 30,248 |
| `Risk 2 (Medium)` | 5,512 |
| `Risk 3 (Low)` | 1,705 |
| `All` | 17 |
| Missing | 7 |

Preserve `All` as a source category. Its meaning has not been confirmed. Keep missing values separate from it.

## Checks before cleaning

- The full download had zero exact duplicate rows, zero repeated nonmissing inspection IDs, and zero missing or unparseable inspection dates. The study window has zero missing inspection IDs. A facility appearing in several inspections is expected.
- Review the complete category lists for `Facility Type`, `Inspection Type`, and `Results` before enforcing any allowed values. Check for leading or trailing spaces and labels that differ only by capitalization before deciding which values to standardize.
- For the binary model, keep `Canvass` records with one of the three completed outcomes above. The audit found 4,009 `Fail` outcomes and 11,863 `Pass` or `Pass w/ Conditions` outcomes. The `Violations` field is recorded during the inspection and must be excluded from pre-inspection features.

## Source

[City of Chicago Data Portal Food Inspections](https://data.cityofchicago.org/Health-Human-Services/Food-Inspections/4ijn-s7e5). Record the actual CSV download date and applicable use terms in the project README.
