from banking.domain.exceptions.invalid_transaction import InvalidTransactionException


class InvalidAmountException(InvalidTransactionException):
    """Exception raised when a transaction amount is invalid."""


class SameAccountTransferException(InvalidTransactionException):
    """Exception raised when a transfer is attempted between the same account."""


class TransactionFailedException(InvalidTransactionException):
    """Exception raised when a transaction fails."""
