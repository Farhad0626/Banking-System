import re
from dataclasses import dataclass

from banking.shared.validators import require_string

_MOBILE_NUMBER_PATTERN = re.compile(
    r"^(?:(?:0|0098|\+98)9(?:0[0-5]|1[0-9]|2[0-3]|3[0-9]|9[0-9])\d{7})$"
)


@dataclass(frozen=True)
class PhoneNumber:
    """Value object representing an Iranian mobile phone number."""

    value: str

    def __post_init__(self) -> None:
        value = require_string(self.value, field_name="Phone number")
        if not _MOBILE_NUMBER_PATTERN.fullmatch(value):
            raise ValueError(f"Phone number '{value}' is invalid.")
