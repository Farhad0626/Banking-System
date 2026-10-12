from banking.domain.exceptions.domain_exception import DomainException


class InsufficientBalanceException(DomainException):
    """Exception raised when there is not enough balance in the account."""
