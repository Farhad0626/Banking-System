from dataclasses import dataclass, field
from datetime import UTC, datetime

from banking.domain.exceptions.customer_exceptions import (
    CustomerInactiveException,
    CustomerRestrictedException,
)
from banking.domain.value_objects.customer_id import CustomerId
from banking.domain.value_objects.national_id import NationalId
from banking.domain.value_objects.phone_number import PhoneNumber


@dataclass
class Customer:
    """Entity representing a customer."""

    id: CustomerId | None
    first_name: str
    last_name: str
    national_id: NationalId
    mobile: PhoneNumber
    email: str
    username: str
    password_hash: str
    is_active: bool
    is_restricted: bool
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = None

    @property
    def is_deleted(self) -> bool:
        """Check if the customer is deleted."""
        return self.deleted_at is not None

    def ensure_can_login(self) -> None:
        """Ensure that the customer can log in."""
        if not self.is_active:
            raise CustomerInactiveException(f"Customer {self.username} is inactive.")
        if self.is_restricted:
            raise CustomerRestrictedException(f"Customer {self.username} is restricted.")

    def activate(self) -> None:
        """Activate the customer."""
        self.is_active = True
        self.updated_at = datetime.now(UTC)

    def restrict(self) -> None:
        """Restrict the customer."""
        self.is_restricted = True
        self.updated_at = datetime.now(UTC)

    def change_password(self, new_password_hash: str) -> None:
        """Change the customer's password."""
        self.password_hash = new_password_hash
        self.updated_at = datetime.now(UTC)

    def mark_deleted(self) -> None:
        """Mark the customer as deleted."""
        self.deleted_at = datetime.now(UTC)
        self.is_active = False
        self.updated_at = datetime.now(UTC)
