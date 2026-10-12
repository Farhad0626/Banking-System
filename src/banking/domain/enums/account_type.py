from enum import Enum


class AccountType(str, Enum):
    """Enum representing the type of a bank account."""

    SAVINGS = "SAVINGS"
    CHECKING = "CHECKING"
    TERM_DEPOSIT = "TERM_DEPOSIT"
