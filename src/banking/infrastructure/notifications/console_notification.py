from banking.application.ports.notifications.notification_sender import NotificationSender


class ConsoleNotificationSender(NotificationSender):
    """Delivers notifications by printing them to the console."""

    def send(self, recipient: str, message: str) -> None:
        """Print a notification line for the given recipient."""
        print(f"[NOTIFICATION] -> {recipient}: {message}")
