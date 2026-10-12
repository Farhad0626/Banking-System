from abc import ABC, abstractmethod
from decimal import Decimal


class ConfigurationService(ABC):
    """Abstract base class for configuration service."""

    @abstractmethod
    def get_int(self, key: str, default: int | None = None) -> int:
        """Retrieve an integer configuration value by key."""
        ...

    @abstractmethod
    def get_decimal(self, key: str, default: Decimal | None = None) -> Decimal:
        """Retrieve a decimal configuration value by key."""
        ...

    @abstractmethod
    def get_str(self, key: str, default: str | None = None) -> str:
        """Retrieve a string configuration value by key."""
        ...

    @abstractmethod
    def get_bool(self, key: str, default: bool | None = None) -> bool:
        """Retrieve a boolean configuration value by key."""
        ...
