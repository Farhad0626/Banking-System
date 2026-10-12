from banking.application.ports.repositories.customer_repository import CustomerRepository
from banking.domain.exceptions.customer_exceptions import CustomerNotFoundException


class ActivateCustomer:
    """Use case for activating a customer account."""

    def __init__(self, customer_repository: CustomerRepository) -> None:
        self._customers = customer_repository

    def execute(self, customer_id: int) -> None:
        """Activates a customer account by setting its is_active status to True."""
        customer = self._customers.get_by_id(customer_id)
        if customer is None or customer.is_deleted:
            raise CustomerNotFoundException(f"Customer with ID {customer_id} not found.")

        customer.activate()
        self._customers.update(customer)
