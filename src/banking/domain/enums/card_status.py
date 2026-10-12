from enum import Enum


class CardStatus(str, Enum):
    """Enum representing the status of a bank card."""

    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
