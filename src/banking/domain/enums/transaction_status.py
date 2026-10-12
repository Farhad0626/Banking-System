from enum import Enum


class TransactionStatus(str, Enum):
    """Enum representing the status of a bank transaction."""

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
