from banking.application.context.session_context import Session
from banking.application.dto.auth.change_password_dto import ChangePasswordRequest
from banking.application.ports.repositories.customer_repository import CustomerRepository
from banking.application.ports.security.password_hasher import PasswordHasher
from banking.domain.exceptions.auth_exceptions import (
    AuthenticationFailedException,
    InvalidCredentialsException,
)
from banking.domain.exceptions.customer_exceptions import CustomerNotFoundException
from banking.domain.value_objects.password import Password


class ChangePassword:
    def __init__(
        self,
        customer_repository: CustomerRepository,
        password_hasher: PasswordHasher,
        password_strict_mode: bool = False,
    ) -> None:
        self._customers = customer_repository
        self._hasher = password_hasher
        self._strict = password_strict_mode

    def execute(self, request: ChangePasswordRequest, session: Session) -> None:
        """Changes the password for an existing customer."""
        if not session.is_owner(request.customer_id):
            raise AuthenticationFailedException("Access to this user account is not permitted.")

        customer = self._customers.get_by_id(request.customer_id)
        if customer is None:
            raise CustomerNotFoundException(f"Customer with ID {request.customer_id} not found.")

        if not self._hasher.verify(request.old_password, customer.password_hash):
            raise InvalidCredentialsException("Current password is incorrect.")

        new_password = Password(plain_value=request.new_password, strict=self._strict)
        if new_password.matches_username(customer.username):
            raise ValueError("New password cannot be the same as the username.")

        hashed_new_password = self._hasher.hash(new_password.plain_value)
        customer.change_password(hashed_new_password)
        self._customers.update(customer)
