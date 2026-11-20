# Muhammad Afnan | 23pwbcs0999 | 20 November 2026

"""Score the two fictional examples from the inference notebook."""

from pathlib import Path

import joblib
import pandas as pd

from src.features import add_calendar_features, prepare_feature_types

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_demo():
    """Load the project's own model and save scores for the fictional examples."""
    model_path = PROJECT_ROOT / "models/chicago_inspection_failure.joblib"
    artifact = joblib.load(model_path)

    new_inspections = pd.DataFrame([
        {
            "Inspection Date": "2025-01-14",
            "Facility Type": "Restaurant",
            "Risk": "Risk 1 (High)",
            "Zip": "60614",
        },
        {
            "Inspection Date": "2025-01-16",
            "Facility Type": "Bakery",
            "Risk": "Risk 2 (Medium)",
            "Zip": None,
        },
    ])

    dates = pd.to_datetime(new_inspections["Inspection Date"], format="%Y-%m-%d")
    features = prepare_feature_types(add_calendar_features(new_inspections, dates))
    features = features[artifact["feature_columns"]]

    probabilities = artifact["pipeline"].predict_proba(features)[:, 1]

    predictions = new_inspections.assign(
        failure_probability=probabilities,
        flag_for_review=probabilities >= artifact["threshold"],
    )

    output_path = PROJECT_ROOT / "outputs/reports/demo_predictions.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(output_path, index=False)
    print(predictions.round(3).to_string(index=False))
    return predictions


if __name__ == "__main__":
    run_demo()
