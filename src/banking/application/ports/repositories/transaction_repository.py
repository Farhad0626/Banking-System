from abc import ABC, abstractmethod
from datetime import datetime

from banking.domain.entities.transaction import Transaction


class TransactionRepository(ABC):
    """Abstract base class for transaction repository."""

    @abstractmethod
    def add(self, transaction: Transaction) -> Transaction:
        """Add a new transaction to the repository."""

    @abstractmethod
    def get_by_id(self, transaction_id: int) -> Transaction | None:
        """Retrieve a transaction by its ID."""

    @abstractmethod
    def get_by_account_id(self, account_id: int) -> list[Transaction]:
        """Retrieve all transactions associated with a given account ID."""

    @abstractmethod
    def search(
        self,
        account_id: int | None = None,
        transaction_type: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[Transaction]:
        """Search for transactions based on a date range."""
