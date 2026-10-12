import getpass
import re
from collections.abc import Callable, Sequence
from datetime import UTC, date, datetime, time

from banking.presentation.console.output_writer import OutputWriter
from banking.shared.validators import normalize_digits as normalize_local_digits

_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩٫", "01234567890123456789.")
_AMOUNT_PATTERN = re.compile(r"^\d+(\.\d{1,2})?$")


class InputCancelled(Exception):
    """Raised when no more input is available (EOF) so the application can exit cleanly."""


class InputReader:
    """Reads and converts user input, re-prompting on invalid values so the app never crashes."""

    def __init__(
        self,
        writer: OutputWriter,
        input_fn: Callable[[str], str] = input,
        password_fn: Callable[[str], str] = getpass.getpass,
    ) -> None:
        """Store the writer and the (injectable) functions used to read input."""
        self._writer = writer
        self._input = input_fn
        self._password = password_fn

    def _read(self, prompt: str) -> str:
        """Read one raw line; end of input is reported as InputCancelled."""
        try:
            return self._input(f"{prompt}: ")
        except EOFError:
            raise InputCancelled from None

    def read_text(
        self, prompt: str, *, default: str | None = None, normalize_digits: bool = False
    ) -> str:
        """Read a non-empty line; Enter keeps the default when one is offered."""
        shown = f"{prompt} [{default}]" if default else prompt
        while True:
            value = self._read(shown).strip()
            if not value and default:
                value = default
            if value:
                return normalize_local_digits(value) if normalize_digits else value
            self._writer.error("This field is required.")

    def read_password(self, prompt: str) -> str:
        """Read a non-empty password without echoing it (never stripped or altered)."""
        while True:
            try:
                value = self._password(f"{prompt}: ")
            except EOFError:
                raise InputCancelled from None
            if value:
                return value
            self._writer.error("Password cannot be empty.")

    def read_choice(self, prompt: str, valid: Sequence[str]) -> str:
        """Read one of the valid options (Persian digits are accepted)."""
        while True:
            value = normalize_local_digits(self._read(prompt).strip())
            if value in valid:
                return value
            self._writer.error(f"Invalid choice. Valid options: {', '.join(valid)}")

    def read_optional_choice(self, prompt: str, valid: Sequence[str]) -> str | None:
        """Read one of the valid words (case-insensitive) or None when the user presses Enter."""
        allowed = {item.upper() for item in valid}
        while True:
            value = self._read(prompt).strip().upper()
            if not value:
                return None
            if value in allowed:
                return value
            self._writer.error(
                f"Invalid value. Valid options: {', '.join(valid)} (or Enter to skip)"
            )

    def read_amount(self, prompt: str) -> str:
        """Read a number with at most two decimals and return it as a normalized string."""
        while True:
            value = normalize_local_digits(self._read(prompt).strip())
            if _AMOUNT_PATTERN.match(value):
                return value
            self._writer.error("Enter a number with at most 2 decimal places (e.g. 150 or 150.50).")

    def read_optional_date(self, prompt: str, *, end_of_day: bool = False) -> datetime | None:
        """Read a YYYY-MM-DD date as a UTC datetime (start or end of that day) or None when skipped."""
        while True:
            value = normalize_local_digits(self._read(prompt).strip())
            if not value:
                return None
            try:
                day = date.fromisoformat(value)
            except ValueError:
                self._writer.error("Use the format YYYY-MM-DD (or press Enter to skip).")
                continue
            return datetime.combine(day, time.max if end_of_day else time.min, tzinfo=UTC)

    def confirm(self, prompt: str) -> bool:
        """Ask a yes/no question."""
        while True:
            value = self._read(f"{prompt} (y/n)").strip().lower()
            if value in {"y", "yes"}:
                return True
            if value in {"n", "no"}:
                return False
            self._writer.error("Please answer y or n.")
