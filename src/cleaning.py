# Muhammad Afnan | 23pwbcs0999 | 20 November 2026

def clean_category_labels(values):
    """Trim surrounding whitespace and mark empty labels as missing."""
    trimmed = values.astype("string").str.strip()
    return trimmed.mask(trimmed.eq(""))


def invalid_coordinates(latitude, longitude):
    """Flag incomplete pairs and coordinates outside valid degree ranges."""
    has_coordinate = latitude.notna() | longitude.notna()
    valid_pair = (
        latitude.between(-90, 90).fillna(False)
        & longitude.between(-180, 180).fillna(False)
    )
    return has_coordinate & ~valid_pair
