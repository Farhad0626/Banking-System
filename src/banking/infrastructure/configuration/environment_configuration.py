import os
from decimal import Decimal, InvalidOperation
from typing import Any, ClassVar

from dotenv import load_dotenv

from banking.application.ports.configuration.configuration_service import ConfigurationService


class ConfigurationError(Exception):
    """Raised when a setting is missing or cannot be converted to the requested type."""


class EnvironmentConfiguration(ConfigurationService):
    """Reads settings from environment variables and the .env file, with optional test overrides."""

    _TRUE: ClassVar[frozenset[str]] = frozenset({"1", "true", "yes", "on"})
    _FALSE: ClassVar[frozenset[str]] = frozenset({"0", "false", "no", "off"})

    def __init__(self, overrides: dict[str, str] | None = None) -> None:
        """Load the .env file and store overrides, which take priority over the environment."""
        load_dotenv()
        self._overrides = dict(overrides or {})

    def _lookup(self, key: str) -> str | None:
        """Return the raw string value for a key, or None if it is unset or empty."""
        value = self._overrides.get(key, os.environ.get(key))
        return None if value is None or value == "" else value

    def _required(self, key: str, default: Any) -> Any:
        """Return the raw value, fall back to the default, or raise if neither exists."""
        value = self._lookup(key)
        if value is not None:
            return value
        if default is None:
            raise ConfigurationError(f"Setting '{key}' is not defined.")
        return default

    def get_str(self, key: str, default: str | None = None) -> str:
        """Return a setting as a string."""
        return str(self._required(key, default))

    def get_int(self, key: str, default: int | None = None) -> int:
        """Return a setting as an integer."""
        raw = self._required(key, default)
        try:
            return int(raw)
        except TypeError, ValueError:
            raise ConfigurationError(f"Setting '{key}' must be an integer.") from None

    def get_decimal(self, key: str, default: Decimal | None = None) -> Decimal:
        """Return a setting as a Decimal (never float, to avoid rounding errors)."""
        raw = self._required(key, default)
        try:
            return Decimal(str(raw))
        except InvalidOperation:
            raise ConfigurationError(f"Setting '{key}' must be a decimal number.") from None

    def get_bool(self, key: str, default: bool | None = None) -> bool:
        """Return a setting as a boolean (accepts true/false, yes/no, on/off, 1/0)."""
        raw = self._lookup(key)
        if raw is None:
            return default if default is not None else False
        normalized = raw.strip().lower()
        if normalized in self._TRUE:
            return True
        if normalized in self._FALSE:
            return False
        raise ConfigurationError(f"Setting '{key}' must be true or false.")
