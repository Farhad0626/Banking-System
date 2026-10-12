import re
from dataclasses import dataclass

from banking.shared.validators import require_string

_EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


@dataclass(frozen=True)
class Email:
    """Value object representing an email address."""

    value: str

    def __post_init__(self) -> None:
        value = require_string(self.value, field_name="Email")
        if not _EMAIL_PATTERN.fullmatch(value):
            raise ValueError(f"Email '{value}' is invalid.")
