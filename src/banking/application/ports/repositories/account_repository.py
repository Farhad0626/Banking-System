from abc import ABC, abstractmethod

from banking.domain.entities.account import Account


class AccountRepository(ABC):
    """Abstract base class for account repository."""

    @abstractmethod
    def add(self, account: Account) -> Account:
        """Add a new account to the repository."""

    @abstractmethod
    def get_by_id(self, account_id: int, for_update: bool = False) -> Account | None:
        """Retrieve an account by its ID."""

    @abstractmethod
    def get_by_account_number(self, account_number: str) -> Account | None:
        """Retrieve an account by its account number."""

    @abstractmethod
    def get_by_customer_id(self, customer_id: int) -> list[Account]:
        """Retrieve all accounts associated with a given customer ID."""

    @abstractmethod
    def search(self, account_type: str | None = None, status: str | None = None) -> list[Account]:
        """Search for accounts based on a query string."""

    @abstractmethod
    def update(self, account: Account) -> None:
        """Update an existing account in the repository."""

    @abstractmethod
    def delete(self, account_id: int) -> None:
        """Delete an account from the repository by its ID."""
