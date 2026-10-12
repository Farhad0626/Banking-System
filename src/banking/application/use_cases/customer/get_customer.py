from banking.application.context.session_context import Session
from banking.application.dto.customer.customer_dto import CustomerView
from banking.application.ports.repositories.customer_repository import CustomerRepository
from banking.domain.exceptions.auth_exceptions import AuthenticationFailedException
from banking.domain.exceptions.customer_exceptions import CustomerNotFoundException


class GetCustomer:
    """Use case for retrieving customer information based on the current session."""

    def __init__(self, customer_repository: CustomerRepository) -> None:
        self._customers = customer_repository

    def execute(self, customer_id: int, session: Session) -> CustomerView:
        if not session.is_owner(customer_id):
            raise AuthenticationFailedException(
                "Access denied: You can only retrieve your own customer information."
            )

        customer = self._customers.get_by_id(customer_id)
        if customer is None or customer.is_deleted:
            raise CustomerNotFoundException(f"Customer with ID {customer_id} not found.")
        if customer.id is None:
            raise RuntimeError("Customer repository returned a customer without an ID.")

        return CustomerView(
            customer_id=customer.id.value,
            first_name=customer.first_name,
            last_name=customer.last_name,
            national_id=customer.national_id.value,
            mobile=customer.mobile.value,
            email=customer.email,
            username=customer.username,
            is_active=customer.is_active,
            is_restricted=customer.is_restricted,
        )
