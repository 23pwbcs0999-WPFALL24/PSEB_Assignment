# Chicago Food Inspections

This project audits Chicago food inspection records and compares classifiers that predict whether a completed routine inspection receives a `Fail` result. Part A covers 37,489 records from 2023–2024. Part B uses 15,872 routine inspections with a recorded final outcome.

## Set up the project

Extract the ZIP and open the `PSEB_Assignment` folder in VS Code. Open a PowerShell terminal in that folder. The dependency pins were verified with Python 3.12. If that version is installed, run:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m src.run_pipeline
.\.venv\Scripts\python.exe -m src.demo_inference
```

On macOS or Linux, use `python3.12 -m venv .venv` and substitute `.venv/bin/python` for the Windows interpreter path. The tests use small fixtures and run without the city CSV. The main command validates the input, saves the Part A results, and fits and evaluates the Part B models. The last command loads the saved model in a new process and scores two fictional inspections.

The two equivalent notebook entry points are in [notebooks](notebooks). To use them, install `ipykernel` in the virtual environment and select that environment as the VS Code kernel. Run `notebooks/assignment.ipynb` first, followed by `notebooks/part2_ass.ipynb`.

## Raw data

The source is the [City of Chicago Food Inspections dataset](https://data.cityofchicago.org/Health-Human-Services/Food-Inspections/4ijn-s7e5). The ZIP includes the original snapshot supplied for this project as `data/raw/Food_Inspections_20261120.csv`. It contains 318,627 records and 17 columns. The pipeline treats it as read-only. Keep a local copy of this snapshot to reproduce the reported figures.

The raw CSV is excluded from Git because of its size. A fresh clone can use the exact snapshot by copying it from the project ZIP to `data/raw/`. To use the current live export instead, run:

```powershell
.\.venv\Scripts\python.exe -m src.download_data
.\.venv\Scripts\python.exe -m src.run_pipeline --raw data/raw/Food_Inspections_live.csv
```

The live export may contain corrections or additional records, so its results can differ. If the portal is unreachable, use its **Export → CSV** option and pass the downloaded path with `--raw`. Verify the city’s applicable data-use terms before redistributing the raw file. The original CSV filename records the snapshot date as 2026-11-20.

## Part A outputs and findings

| Output | Finding or contents |
| --- | --- |
| [Monthly routine failure rate](outputs/figures/monthly_routine_failure_rate.png) | The failure rate among completed routine inspections fell from 27.7% in 2023 to 23.2% in 2024. |
| [Inspection outcome counts](outputs/figures/inspection_outcome_counts.png) | Pass was the most frequently recorded result across the full study window. |
| [Blank violations by outcome](outputs/figures/blank_violations_by_outcome.png) | Violation details were blank for 96.1% of No Entry records and for 172 recorded failures. |
| [Facility ranking](outputs/reports/facility_failure_rates.csv) | Long Term Care had the highest rate among named facility types with at least 50 completed routine inspections (71 of 227, or 31.3%). The [SQLite query](sql/facility_failure_rates.sql) shows the calculation. |
| [Data-quality summary](outputs/reports/data_quality_summary.csv) | All 37,489 study records were retained. There were zero duplicate rows and 126 missing coordinate pairs. The [per-column report](outputs/reports/data_quality_by_column.csv) compares missingness before and after cleaning. |

The cleaned CSV is written to `data/cleaned/food_inspections_2023_2024.csv`.

## Part B outputs and findings

Training used 2023, followed by validation on January–June 2024 and a held-out test on July–December 2024. The [model comparison](outputs/reports/model_comparison.csv) includes the dummy baseline, logistic regression, and random forest. In the [final test](outputs/reports/final_test_metrics.csv), logistic regression achieved 0.228 average precision versus 0.213 for the dummy baseline and missed 750 of 942 failures. The results provide insufficient evidence for operational inspection decisions.

The fitted model and its validation-selected threshold are saved in `models/chicago_inspection_failure.joblib`. The inference demo writes [two example predictions](outputs/reports/demo_predictions.csv).

## Project documentation

- [Raw data schema](docs/schema.md)
- [Cleaning assumptions and model card](docs/assumptions.md)
- [Part C exploration checklist](docs/exploration.md), for the independent exercises

ChatGPT assisted with explanations, debugging, organizing the existing notebook code, and drafting project documentation. The reported results were generated from the supplied Chicago dataset.
