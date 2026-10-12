from banking.domain.exceptions.domain_exception import DomainException


class CustomerNotFoundException(DomainException):
    """Exception raised when a customer is not found."""


class DuplicateNationalIdException(DomainException):
    """Exception raised when a customer with the same national ID already exists."""


class DuplicateMobileException(DomainException):
    """Exception raised when a customer with the same mobile number already exists."""


class DuplicateUsernameException(DomainException):
    """Exception raised when a customer with the same username already exists."""


class CustomerInactiveException(DomainException):
    """Exception raised when an operation is attempted on an inactive customer."""


class CustomerRestrictedException(DomainException):
    """Exception raised when an operation is attempted on a restricted customer."""
