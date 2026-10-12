from banking.application.dto.customer.customer_dto import CustomerView, SearchCustomerRequest
from banking.application.ports.repositories.customer_repository import CustomerRepository


class SearchCustomers:
    """Use case for searching customers based on specific criteria."""

    def __init__(self, customer_repository: CustomerRepository) -> None:
        self._customers = customer_repository

    def execute(self, request: SearchCustomerRequest) -> list[CustomerView]:
        """Searches for customers based on the provided keyword."""
        customers = self._customers.search(keyword=request.keyword)
        result = []
        for customer in customers:
            if customer.id is None:
                raise RuntimeError("Customer repository returned a customer without an ID.")
            customer_view = CustomerView(
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
            result.append(customer_view)
        return result
