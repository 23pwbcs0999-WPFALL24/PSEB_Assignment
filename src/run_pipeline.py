# Muhammad Afnan | 23pwbcs0999 | 20 November 2026

"""Rebuild the audit reports, charts, and fitted model from the source CSV."""

import argparse
from contextlib import closing
from pathlib import Path
import sqlite3

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.cleaning import clean_category_labels, invalid_coordinates
from src.features import (
    add_calendar_features,
    categorical_features,
    feature_columns,
    numeric_features,
    prepare_feature_types,
)
from src.validation import validate_raw_input

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_CSV = PROJECT_ROOT / "data/raw/Food_Inspections_20261120.csv"


def run_analysis(raw_csv):
    """Clean the study window, save Part A outputs, and return the ML cohort."""
    df = pd.read_csv(raw_csv, dtype={"Zip": "string", "License #": "string"})
    dates = validate_raw_input(df)
    print(f"Raw input passed: {len(df):,} rows.")
    study = df.loc[dates.dt.year.isin([2023, 2024])].copy()
    if study.empty:
        raise ValueError("No records were found in the 2023–2024 study window.")
    inspection_dates = dates.loc[study.index]
    print(f"Study rows: {len(study):,}")

    violation_audit = (
        study.assign(violation_missing=study["Violations"].isna())
        .groupby("Results")["violation_missing"]
        .agg(total_rows="size", blank_violations="sum")
    )

    violation_audit["blank_pct"] = (
        100 * violation_audit["blank_violations"] / violation_audit["total_rows"]
    ).round(1)

    print(violation_audit.to_string())

    category_columns = ["Facility Type", "Risk", "Inspection Type", "Results"]
    cleaned = study.copy()

    for column in category_columns:
        cleaned[column] = clean_category_labels(study[column])

    comparison = pd.DataFrame({
        "missing_before": study[category_columns].isna().sum(),
        "missing_after": cleaned[category_columns].isna().sum(),
        "unique_before": study[category_columns].nunique(),
        "unique_after": cleaned[category_columns].nunique(),
    })

    assert len(cleaned) == len(study), "Cleaning changed the row count."
    print(comparison.to_string())

    bad_coordinates = invalid_coordinates(cleaned["Latitude"], cleaned["Longitude"])
    both_missing = cleaned[["Latitude", "Longitude"]].isna().all(axis=1)

    print("Rows with both coordinates missing:", both_missing.sum())
    print("Rows with invalid or incomplete coordinates:", bad_coordinates.sum())

    identifiers = study[["Zip", "License #"]]

    for column, pattern in {"Zip": r"[0-9]{5}", "License #": r"[0-9]+"}.items():
        values = identifiers[column].str.strip()
        unusual = values.notna() & ~values.str.fullmatch(pattern, na=False)

        print(f"\n{column}")
        print("Missing:", values.isna().sum())
        print("Values outside the expected format:", unusual.sum())
        print("Examples:", values[unusual].value_counts().head(5).to_dict())

    # Use the parsed dates and the identifiers read directly as text.
    cleaned["Inspection Date"] = inspection_dates
    for column in ["Zip", "License #"]:
        cleaned[column] = identifiers[column].str.strip()

    # Build the summary cohort without removing rows from the cleaned dataset.
    final_outcomes = ["Pass", "Pass w/ Conditions", "Fail"]
    is_routine = cleaned["Inspection Type"].str.casefold().eq("canvass").fillna(False)
    has_final_outcome = cleaned["Results"].isin(final_outcomes)
    routine_completed = cleaned.loc[is_routine & has_final_outcome].copy()

    routine_completed["month"] = (
        routine_completed["Inspection Date"].dt.to_period("M").astype(str)
    )
    routine_completed["failed"] = np.where(
        routine_completed["Results"].eq("Fail").to_numpy(dtype=bool), 1, 0
    )

    monthly = routine_completed.groupby("month", as_index=False).agg(
        completed_inspections=("failed", "size"),
        failures=("failed", "sum"),
    )
    monthly["failure_rate_pct"] = 100 * np.divide(
        monthly["failures"], monthly["completed_inspections"]
    )

    (PROJECT_ROOT / "data/cleaned").mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "outputs/reports").mkdir(parents=True, exist_ok=True)

    cleaned.to_csv((PROJECT_ROOT / "data/cleaned/food_inspections_2023_2024.csv"), index=False)
    monthly.to_csv((PROJECT_ROOT / "outputs/reports/monthly_routine_failures.csv"), index=False)

    print(monthly.round({"failure_rate_pct": 1}).to_string(index=False))

    figure_dir = PROJECT_ROOT / "outputs/figures"
    figure_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(pd.to_datetime(monthly["month"]), monthly["failure_rate_pct"], marker="o")
    ax.set(
        title="Monthly failure rate among completed routine inspections",
        xlabel="Inspection month",
        ylabel="Failure rate (%)",
    )
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(figure_dir / "monthly_routine_failure_rate.png", dpi=160)
    plt.close(fig)

    outcomes = cleaned["Results"].value_counts().sort_values()
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.barh(outcomes.index, outcomes.values)
    ax.set(
        title="Recorded inspection outcomes in 2023–2024",
        xlabel="Inspection records (count)",
        ylabel="Recorded outcome",
    )
    fig.tight_layout()
    fig.savefig(figure_dir / "inspection_outcome_counts.png", dpi=160)
    plt.close(fig)

    blanks = violation_audit["blank_pct"].sort_values()
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.barh(blanks.index, blanks.values)
    ax.set(
        title="Blank violation entries by recorded outcome",
        xlabel="Inspection records with blank violation details (%)",
        ylabel="Recorded outcome",
        xlim=(0, 105),
    )
    fig.tight_layout()
    fig.savefig(figure_dir / "blank_violations_by_outcome.png", dpi=160)
    plt.close(fig)

    query = """
    SELECT
        facility_type,
        COUNT(*) AS completed_inspections,
        SUM(failed) AS failures,
        ROUND(100.0 * SUM(failed) / COUNT(*), 1) AS failure_rate_pct
    FROM routine_inspections
    WHERE facility_type IS NOT NULL
    GROUP BY facility_type
    HAVING COUNT(*) >= 50
    ORDER BY 1.0 * SUM(failed) / COUNT(*) DESC,
             completed_inspections DESC,
             facility_type
    LIMIT 10;
    """

    (PROJECT_ROOT / "sql").mkdir(exist_ok=True)
    (PROJECT_ROOT / "sql/facility_failure_rates.sql").write_text(query.strip() + "\n", encoding="utf-8")

    sql_input = routine_completed[["Facility Type", "failed"]].rename(
        columns={"Facility Type": "facility_type"}
    )

    with closing(sqlite3.connect(":memory:")) as connection:
        sql_input.to_sql("routine_inspections", connection, index=False)
        facility_rates = pd.read_sql_query(query, connection)

    facility_rates.to_csv((PROJECT_ROOT / "outputs/reports/facility_failure_rates.csv"), index=False)
    print(facility_rates.to_string(index=False))

    report_dir = PROJECT_ROOT / "outputs/reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    quality_by_column = pd.DataFrame({
        "missing_before": study.isna().sum(),
        "missing_after": cleaned.isna().sum(),
    })
    quality_by_column["missing_pct_before"] = (
        100 * quality_by_column["missing_before"] / len(study)
    ).round(2)
    quality_by_column["missing_pct_after"] = (
        100 * quality_by_column["missing_after"] / len(cleaned)
    ).round(2)

    quality_summary = pd.Series({
        "study_rows_before_cleaning": len(study),
        "study_rows_after_cleaning": len(cleaned),
        "rows_removed_during_cleaning": len(study) - len(cleaned),
        "exact_duplicates_before": study.duplicated().sum(),
        "exact_duplicates_after": cleaned.duplicated().sum(),
        "missing_inspection_ids": cleaned["Inspection ID"].isna().sum(),
        "repeated_nonmissing_inspection_ids": (
            cleaned["Inspection ID"].dropna().duplicated().sum()
        ),
        "unparseable_or_missing_dates_after": cleaned["Inspection Date"].isna().sum(),
        "missing_coordinate_pairs": (
            cleaned[["Latitude", "Longitude"]].isna().all(axis=1).sum()
        ),
        "invalid_or_incomplete_coordinate_pairs": invalid_coordinates(
            cleaned["Latitude"], cleaned["Longitude"]
        ).sum(),
    }, name="count")

    quality_by_column.to_csv(report_dir / "data_quality_by_column.csv", index_label="column")
    quality_summary.to_csv(report_dir / "data_quality_summary.csv", index_label="check")
    violation_audit.to_csv(report_dir / "blank_violations_by_outcome.csv")

    print(quality_summary.to_string())

    return routine_completed


def run_modeling(routine_completed):
    """Compare models chronologically and save the selected pipeline."""
    model_data = add_calendar_features(routine_completed, routine_completed["Inspection Date"])
    inspection_dates = model_data["Inspection Date"]
    train_end = pd.Timestamp("2024-01-01")
    validation_end = pd.Timestamp("2024-07-01")

    split_masks = {
        "train": inspection_dates < train_end,
        "validation": (inspection_dates >= train_end) & (inspection_dates < validation_end),
        "test": inspection_dates >= validation_end,
    }

    splits = {}
    for name, mask in split_masks.items():
        X = model_data.loc[mask, feature_columns].copy()
        y = model_data.loc[mask, "failed"].copy()
        if y.nunique() != 2:
            raise ValueError(f"The {name} split needs both outcome classes.")
        splits[name] = (X, y)
        print(f"{name:10s} {len(y):,} rows | {y.sum():,} failures | {y.mean():.1%}")

    X_train, y_train = splits["train"]
    X_validation, y_validation = splits["validation"]
    X_train = prepare_feature_types(X_train)
    X_validation = prepare_feature_types(X_validation)

    preprocessor = ColumnTransformer([
        ("categorical", Pipeline([
            ("impute", SimpleImputer(strategy="constant", fill_value="Missing")),
            ("encode", OneHotEncoder(handle_unknown="ignore")),
        ]), categorical_features),
        ("numeric", Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]), numeric_features),
    ])

    models = {
        "Dummy baseline": DummyClassifier(strategy="prior"),
        "Logistic regression": LogisticRegression(max_iter=1000),
        "Random forest": RandomForestClassifier(
            n_estimators=200, min_samples_leaf=5, random_state=42, n_jobs=-1
        ),
    }

    fitted_models = {}
    scores = []

    for name, estimator in models.items():
        pipeline = Pipeline([
            ("preprocess", clone(preprocessor)),
            ("model", estimator),
        ])
        pipeline.fit(X_train, y_train)
        fitted_models[name] = pipeline

        probabilities = pipeline.predict_proba(X_validation)[:, 1]
        predictions = pipeline.predict(X_validation)

        scores.append({
            "model": name,
            "average_precision": average_precision_score(y_validation, probabilities),
            "roc_auc": roc_auc_score(y_validation, probabilities),
            "precision": precision_score(y_validation, predictions, zero_division=0),
            "recall": recall_score(y_validation, predictions, zero_division=0),
            "f1": f1_score(y_validation, predictions, zero_division=0),
        })

    model_comparison = pd.DataFrame(scores).sort_values(
        "average_precision", ascending=False
    )
    print(model_comparison.round(3).to_string(index=False))

    candidate = fitted_models["Logistic regression"]
    validation_prob = candidate.predict_proba(X_validation)[:, 1]

    review_threshold = float(np.quantile(validation_prob, 0.80))
    thresholds = {"Default": 0.50, "Approx. 20% flagged": review_threshold}

    rows = []
    for name, threshold in thresholds.items():
        predicted = (validation_prob >= threshold).astype(int)
        tn, fp, fn, tp = confusion_matrix(
            y_validation, predicted, labels=[0, 1]
        ).ravel()

        rows.append({
            "rule": name,
            "threshold": threshold,
            "flagged_pct": 100 * predicted.mean(),
            "true_positives": tp,
            "false_positives": fp,
            "missed_failures": fn,
            "precision": precision_score(y_validation, predicted, zero_division=0),
            "recall": recall_score(y_validation, predicted, zero_division=0),
        })

    threshold_comparison = pd.DataFrame(rows)
    threshold_comparison.to_csv(
        (PROJECT_ROOT / "outputs/reports/validation_threshold_comparison.csv"), index=False
    )
    print(threshold_comparison.round(3).to_string(index=False))

    # Of the inspections that actually failed, how many did the model miss by risk group?
    errors = X_validation[["Risk"]].copy()
    errors["actual_failure"] = y_validation.to_numpy() == 1
    errors["missed_failure"] = errors["actual_failure"] & (
        validation_prob < review_threshold
    )

    by_risk = errors.groupby("Risk", dropna=False).agg(
        actual_failures=("actual_failure", "sum"),
        missed_failures=("missed_failure", "sum"),
    )
    by_risk["missed_pct"] = (
        100 * by_risk["missed_failures"]
        / by_risk["actual_failures"].replace(0, np.nan)
    )

    by_risk.to_csv((PROJECT_ROOT / "outputs/reports/validation_errors_by_risk.csv"))
    print("\nValidation errors by risk group:")
    print(by_risk.round(1).to_string())

    train_dates = model_data.loc[X_train.index, "Inspection Date"]

    fold_windows = [
        ("Jul–Aug", "2023-07-01", "2023-09-01"),
        ("Sep–Oct", "2023-09-01", "2023-11-01"),
        ("Nov–Dec", "2023-11-01", "2024-01-01"),
    ]

    fold_rows = []

    for fold_name, start, end in fold_windows:
        start = pd.Timestamp(start)
        end = pd.Timestamp(end)

        fit_rows = train_dates < start
        score_rows = (train_dates >= start) & (train_dates < end)
        y_fold = y_train.loc[score_rows]
        if y_fold.nunique() != 2 or y_train.loc[fit_rows].nunique() != 2:
            raise ValueError(f"Fold {fold_name} needs both classes on each side of the split.")

        for name, fitted_pipeline in fitted_models.items():
            # Clone the pipeline so preprocessing is fitted anew in each fold.
            fold_pipeline = clone(fitted_pipeline)
            fold_pipeline.fit(X_train.loc[fit_rows], y_train.loc[fit_rows])
            probabilities = fold_pipeline.predict_proba(X_train.loc[score_rows])[:, 1]

            fold_rows.append({
                "fold": fold_name,
                "model": name,
                "evaluation_rows": len(y_fold),
                "failure_rate": y_fold.mean(),
                "average_precision": average_precision_score(y_fold, probabilities),
                "roc_auc": roc_auc_score(y_fold, probabilities),
            })

    fold_results = pd.DataFrame(fold_rows)
    cv_summary = fold_results.groupby("model", as_index=False).agg(
        cv_avg_precision_mean=("average_precision", "mean"),
        cv_avg_precision_std=("average_precision", "std"),
        cv_roc_auc_mean=("roc_auc", "mean"),
    )

    comparison = model_comparison.rename(columns={
        "average_precision": "validation_average_precision",
        "roc_auc": "validation_roc_auc",
        "precision": "validation_precision",
        "recall": "validation_recall",
        "f1": "validation_f1",
    }).merge(cv_summary, on="model")

    fold_results.to_csv((PROJECT_ROOT / "outputs/reports/time_cv_folds.csv"), index=False)
    comparison.to_csv((PROJECT_ROOT / "outputs/reports/model_comparison.csv"), index=False)

    print(fold_results.round(3).to_string(index=False))
    print("\nCombined comparison:")
    print(comparison.round(3).to_string(index=False))

    X_test, y_test = splits["test"]
    X_test = prepare_feature_types(X_test)

    final_pipeline = fitted_models["Logistic regression"]
    test_probabilities = final_pipeline.predict_proba(X_test)[:, 1]
    test_predictions = (test_probabilities >= review_threshold).astype(int)

    test_metrics = pd.DataFrame([{
        "model": "Logistic regression",
        "threshold": review_threshold,
        "test_rows": len(y_test),
        "actual_failures": int(y_test.sum()),
        "dummy_average_precision": y_test.mean(),
        "average_precision": average_precision_score(y_test, test_probabilities),
        "roc_auc": roc_auc_score(y_test, test_probabilities),
        "flagged_pct": 100 * test_predictions.mean(),
        "precision": precision_score(y_test, test_predictions, zero_division=0),
        "recall": recall_score(y_test, test_predictions, zero_division=0),
        "f1": f1_score(y_test, test_predictions, zero_division=0),
    }])

    test_confusion = pd.DataFrame(
        confusion_matrix(y_test, test_predictions, labels=[0, 1]),
        index=["Actual non-fail", "Actual fail"],
        columns=["Predicted non-fail", "Predicted fail"],
    )

    test_metrics.to_csv((PROJECT_ROOT / "outputs/reports/final_test_metrics.csv"), index=False)
    test_confusion.to_csv((PROJECT_ROOT / "outputs/reports/final_test_confusion_matrix.csv"))

    print(test_metrics.round(3).to_string(index=False))
    print("\nFinal test confusion matrix:")
    print(test_confusion.to_string())

    (PROJECT_ROOT / "models").mkdir(exist_ok=True)

    joblib.dump(
        {
            "pipeline": final_pipeline,
            "threshold": float(review_threshold),
            "feature_columns": feature_columns,
        },
        (PROJECT_ROOT / "models/chicago_inspection_failure.joblib"),
    )

    print("Saved models/chicago_inspection_failure.joblib")


def main():
    """Read the raw path from the command line and run both project parts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=DEFAULT_RAW_CSV)
    args = parser.parse_args()
    if not args.raw.is_file():
        parser.error(f"CSV not found: {args.raw}. See the README for download instructions.")
    run_modeling(run_analysis(args.raw))


if __name__ == "__main__":
    main()
