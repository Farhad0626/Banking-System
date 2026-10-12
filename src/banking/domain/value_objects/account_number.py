import re
from dataclasses import dataclass

from banking.shared.validators import require_string

_ACCOUNT_NUMBER_PATTERN = re.compile(r"^[0-9]{16}$")


@dataclass(frozen=True)
class AccountNumber:
    """Value object representing an account number."""

    value: str

    def __post_init__(self) -> None:
        value = require_string(self.value, field_name="Account number")
        if not _ACCOUNT_NUMBER_PATTERN.fullmatch(value):
            raise ValueError(f"Account number '{value}' does not have a valid format.")
