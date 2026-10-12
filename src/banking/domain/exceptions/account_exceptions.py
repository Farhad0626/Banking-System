from banking.domain.exceptions.domain_exception import DomainException
from banking.domain.exceptions.insufficient_balance import InsufficientBalanceException
from banking.domain.exceptions.invalid_account_state import InvalidAccountStateException


class AccountNotFoundException(DomainException):
    """Exception raised when an account is not found."""


class AccountInactiveException(InvalidAccountStateException):
    """Exception raised when an account is inactive."""


class InvalidAccountOperationException(InvalidAccountStateException):
    """Exception raised when an invalid operation is attempted on an account."""


__all__ = [
    "AccountInactiveException",
    "AccountNotFoundException",
    "InsufficientBalanceException",
    "InvalidAccountOperationException",
]
