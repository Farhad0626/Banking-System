from abc import ABC, abstractmethod


class RateLimiter(ABC):
    """Abstract base class for rate limiting functionality."""

    @abstractmethod
    def is_locked(self, key: str) -> bool:
        """Check if the given key is currently locked due to rate limiting."""
        ...

    @abstractmethod
    def register_failure(self, key: str) -> None:
        """Register a failed attempt for the given key."""
        ...

    @abstractmethod
    def reset(self, key: str) -> None:
        """Reset the rate limit for the given key."""
        ...
