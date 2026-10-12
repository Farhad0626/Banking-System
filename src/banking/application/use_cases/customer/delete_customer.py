from banking.application.ports.persistence.unit_of_work import UnitOfWork
from banking.domain.exceptions.customer_exceptions import CustomerNotFoundException


class DeleteCustomer:
    """Application use case for soft-deleting a customer and deactivating their accounts."""

    def __init__(self, unit_of_work: UnitOfWork) -> None:
        self._uow = unit_of_work

    def execute(self, customer_id: int) -> None:
        with self._uow as uow:
            customer = uow.customers.get_by_id(customer_id)
            if customer is None:
                raise CustomerNotFoundException(f"Customer with ID {customer_id} not found.")

            customer.mark_deleted()
            uow.customers.update(customer)

            for account in uow.accounts.get_by_customer_id(customer_id):
                account.deactivate()
                uow.accounts.update(account)

            uow.commit()
