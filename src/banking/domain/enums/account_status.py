from enum import Enum


class AccountStatus(str, Enum):
    """Enum representing the status of a bank account."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DELETED = "DELETED"
