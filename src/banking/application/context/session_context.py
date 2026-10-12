from dataclasses import dataclass
from datetime import datetime

from banking.domain.exceptions.auth_exceptions import AuthenticationFailedException


@dataclass
class Session:
    """Identity of the logged-in customer; becomes unusable once invalidated at logout."""

    customer_id: int
    role: str
    authenticated_at: datetime
    is_active: bool = True

    def invalidate(self) -> None:
        """Mark the session as ended; every ownership check fails afterwards."""
        self.is_active = False

    def require_active(self) -> None:
        """Raise AuthenticationFailed if the session has been invalidated."""
        if not self.is_active:
            raise AuthenticationFailedException("Your session has ended. Please log in again.")

    def is_owner(self, customer_id: int) -> bool:
        """Return True only for an active session whose customer matches the given id."""
        return self.is_active and self.customer_id == customer_id
