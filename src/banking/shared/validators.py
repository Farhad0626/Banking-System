"""Shared validation and normalization helpers for user-supplied values."""

_LOCAL_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩٫", "01234567890123456789.")


def require_string(value: object, *, field_name: str) -> str:
    """Return a string value or raise a consistent type error."""
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string.")
    return value


def normalize_digits(value: str) -> str:
    """Convert Persian/Arabic digits and decimal separators to plain ASCII digits."""
    return value.translate(_LOCAL_DIGITS)
