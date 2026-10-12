import re
from dataclasses import dataclass

from banking.shared.validators import require_string


@dataclass(frozen=True)
class Password:
    """Value object representing a password."""

    plain_value: str
    strict: bool = False

    def __post_init__(self) -> None:
        value = require_string(self.plain_value, field_name="Password")
        if len(value.encode("utf-8")) > 72:
            raise ValueError("The password must not exceed 72 bytes.")
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one digit.")
        if self.strict and not re.search(r"[@$!%*?&]", value):
            raise ValueError("Password must contain at least one special character (@$!%*?&).")

    def matches_username(self, username: str) -> bool:
        """Check if the password matches the given username."""
        return self.plain_value.lower() == username.lower()
