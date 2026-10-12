from abc import ABC, abstractmethod


class NotificationSender(ABC):
    """Abstract base class for sending notifications."""

    @abstractmethod
    def send(self, recipient: str, message: str) -> None:
        """Send a notification to the specified recipient with the given message."""
        ...
