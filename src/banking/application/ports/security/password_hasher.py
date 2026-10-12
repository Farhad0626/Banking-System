from abc import ABC, abstractmethod


class PasswordHasher(ABC):
    """Abstract base class for password hashing and verification."""

    @abstractmethod
    def hash(self, plain_password: str) -> str:
        """Hash a plain password and return the hashed version."""
        ...

    @abstractmethod
    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against a hashed password."""
        ...
