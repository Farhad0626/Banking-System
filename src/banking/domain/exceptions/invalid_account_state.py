from banking.domain.exceptions.domain_exception import DomainException


class InvalidAccountStateException(DomainException):
    """Exception raised when an operation is attempted on an account that is in an invalid state."""
