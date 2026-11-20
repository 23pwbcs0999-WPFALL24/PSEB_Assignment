# Muhammad Afnan | 23pwbcs0999 | 20 November 2026

import numpy as np

categorical_features = ["Facility Type", "Risk", "Zip"]
numeric_features = ["inspection_month", "inspection_weekday"]
feature_columns = categorical_features + numeric_features


def add_calendar_features(frame, dates):
    """Create month and weekday features from dates already parsed by the caller."""
    result = frame.copy()
    result["inspection_month"] = dates.dt.month
    result["inspection_weekday"] = dates.dt.dayofweek
    return result


def prepare_feature_types(features):
    """Expose missing categorical values as np.nan for scikit-learn."""
    result = features.copy()
    categories = result[categorical_features].astype(object)
    result[categorical_features] = categories.where(categories.notna(), np.nan)
    return result
