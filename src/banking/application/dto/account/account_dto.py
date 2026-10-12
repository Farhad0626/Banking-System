from dataclasses import dataclass


@dataclass
class CreateAccountRequest:
    """Data transfer object for creating a new account."""

    customer_id: int
    account_type: str
    initial_deposit: str = "0"


@dataclass
class AccountView:
    """Data transfer object for viewing account details."""

    account_id: int
    customer_id: int
    account_number: str
    account_type: str
    balance: str
    status: str


@dataclass
class AccountLookupView:
    """Minimal public data returned when resolving a destination account number."""

    account_id: int
    account_number: str
