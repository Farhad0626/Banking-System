from abc import ABC, abstractmethod


class PinHasher(ABC):
    """Abstract base class for PIN hashing and verification."""

    @abstractmethod
    def hash(self, pin: str) -> str:
        """Hash a PIN and return the hashed version."""
        ...

    @abstractmethod
    def verify(self, pin: str, hashed_pin: str) -> bool:
        """Verify a PIN against a hashed PIN."""
        ...
