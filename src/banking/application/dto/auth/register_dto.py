from dataclasses import dataclass


@dataclass
class RegisterCustomerRequest:
    """Data transfer object for registering a new customer."""

    first_name: str
    last_name: str
    national_id: str
    mobile: str
    email: str
    username: str
    password: str


@dataclass
class RegisterCustomerResult:
    """Data transfer object for the result of registering a new customer."""

    customer_id: int
    username: str
