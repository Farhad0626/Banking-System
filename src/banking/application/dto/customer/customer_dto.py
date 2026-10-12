from dataclasses import dataclass


@dataclass
class CustomerView:
    """Data transfer object for viewing customer information."""

    customer_id: int
    first_name: str
    last_name: str
    national_id: str
    mobile: str
    email: str
    username: str
    is_active: bool
    is_restricted: bool


@dataclass
class SearchCustomerRequest:
    """Data transfer object for searching customers."""

    keyword: str | None = None
