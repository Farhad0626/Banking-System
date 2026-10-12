from enum import Enum


class TransactionType(str, Enum):
    """Enum representing the type of a bank transaction."""

    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRANSFER = "TRANSFER"
