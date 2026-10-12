from banking.domain.exceptions.domain_exception import DomainException


class InvalidTransactionException(DomainException):
    """Exception raised when a transaction is invalid."""
