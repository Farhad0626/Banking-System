from banking.domain.exceptions.domain_exception import DomainException


class InvalidCredentialsException(DomainException):
    """Exception raised when user credentials are invalid."""


class AuthenticationFailedException(DomainException):
    """Exception raised when authentication fails."""


class AccountLockedException(DomainException):
    """Exception raised when an account is locked due to multiple failed login attempts."""
