import re
from dataclasses import dataclass

from banking.shared.validators import require_string

_NATIONAL_ID_PATTERN = re.compile(r"[0-9]{10}")


def _is_valid_national_id(value: str) -> bool:
    """Check whether an Iranian national ID is valid."""

    if not _NATIONAL_ID_PATTERN.fullmatch(value):
        return False

    digits = [int(number) for number in value]

    total = sum(digits[index] * (10 - index) for index in range(9))

    remainder = total % 11

    if remainder < 2:
        expected_check_digit = remainder
    else:
        expected_check_digit = 11 - remainder

    actual_check_digit = digits[9]

    return actual_check_digit == expected_check_digit


@dataclass(frozen=True)
class NationalId:
    """Value object representing an Iranian national ID."""

    value: str

    def __post_init__(self) -> None:
        value = require_string(self.value, field_name="National ID")
        if not _is_valid_national_id(value):
            raise ValueError(f"National ID '{value}' is invalid.")
