from dataclasses import dataclass


@dataclass
class ChangePasswordRequest:
    """Data transfer object for changing a customer's password."""

    customer_id: int
    old_password: str
    new_password: str
