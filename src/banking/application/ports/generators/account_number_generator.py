from abc import ABC, abstractmethod


class AccountNumberGenerator(ABC):
    """Abstract base class for generating account numbers."""

    @abstractmethod
    def generate(self) -> str:
        """Generate a new account number."""
        ...
