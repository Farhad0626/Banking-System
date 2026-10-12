from abc import ABC, abstractmethod

from banking.domain.entities.customer import Customer


class CustomerRepository(ABC):
    """Abstract base class for customer repository."""

    @abstractmethod
    def add(self, customer: Customer) -> Customer:
        """Add a new customer to the repository."""

    @abstractmethod
    def get_by_id(self, customer_id: int) -> Customer | None:
        """Retrieve a customer by their ID."""

    @abstractmethod
    def get_by_username(self, username: str) -> Customer | None:
        """Retrieve a customer by their username."""

    @abstractmethod
    def get_by_national_id(self, national_id: str) -> Customer | None:
        """Retrieve a customer by their national ID."""

    @abstractmethod
    def get_by_mobile(self, mobile: str) -> Customer | None:
        """Retrieve a customer by their mobile number."""

    @abstractmethod
    def search(self, keyword: str | None = None) -> list[Customer]:
        """Search for customers based on a query string."""

    @abstractmethod
    def update(self, customer: Customer) -> None:
        """Update an existing customer in the repository."""

    @abstractmethod
    def delete(self, customer_id: int) -> None:
        """Delete a customer from the repository by their ID."""
