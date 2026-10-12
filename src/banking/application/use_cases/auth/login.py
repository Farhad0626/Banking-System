from datetime import UTC, datetime

from banking.application.context.session_context import Session
from banking.application.dto.auth.login_dto import LoginRequest, LoginResult
from banking.application.ports.repositories.customer_repository import CustomerRepository
from banking.application.ports.security.password_hasher import PasswordHasher
from banking.application.ports.security.rate_limiter import RateLimiter
from banking.domain.exceptions.auth_exceptions import (
    AccountLockedException,
    InvalidCredentialsException,
)


class Login:
    def __init__(
        self,
        customer_repository: CustomerRepository,
        password_hasher: PasswordHasher,
        rate_limiter: RateLimiter,
    ) -> None:
        self._customers = customer_repository
        self._hasher = password_hasher
        self._rate_limiter = rate_limiter

    def execute(self, request: LoginRequest) -> tuple[LoginResult, Session]:
        """Authenticates a customer and returns a session token."""
        if self._rate_limiter.is_locked(request.username):
            raise AccountLockedException(
                f"Account for username {request.username} is locked due to multiple failed login attempts."
            )

        customer = self._customers.get_by_username(request.username)
        if customer is None or customer.is_deleted:
            self._rate_limiter.register_failure(request.username)
            raise InvalidCredentialsException("Invalid username or password.")
        customer.ensure_can_login()
        if not self._hasher.verify(request.password, customer.password_hash):
            self._rate_limiter.register_failure(request.username)
            raise InvalidCredentialsException("Invalid username or password.")
        if customer.id is None:
            raise RuntimeError("Customer repository returned a customer without an ID.")

        self._rate_limiter.reset(request.username)
        session = Session(
            customer_id=customer.id.value, role="CUSTOMER", authenticated_at=datetime.now(UTC)
        )
        result = LoginResult(customer_id=customer.id.value, role=session.role)
        return result, session
