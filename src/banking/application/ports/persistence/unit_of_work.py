from abc import ABC, abstractmethod
from types import TracebackType
from typing import Self

from banking.application.ports.repositories.account_repository import AccountRepository
from banking.application.ports.repositories.customer_repository import CustomerRepository
from banking.application.ports.repositories.transaction_repository import TransactionRepository


class UnitOfWork(ABC):
    """
    A context manager to ensure the atomicity of multi-repository operations
    (such as a Transfer involving both two accounts and a transaction).
    """

    customers: CustomerRepository
    accounts: AccountRepository
    transactions: TransactionRepository

    @abstractmethod
    def __enter__(self) -> Self:
        """Enter the runtime context related to this object."""
        ...

    @abstractmethod
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Exit the runtime context related to this object."""
        ...

    @abstractmethod
    def commit(self) -> None:
        """Commit the current transaction."""
        ...

    @abstractmethod
    def rollback(self) -> None:
        """Rollback the current transaction."""
        ...
