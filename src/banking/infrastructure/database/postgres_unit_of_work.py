import logging
from types import TracebackType
from typing import Self

from banking.application.ports.persistence.unit_of_work import UnitOfWork
from banking.infrastructure.database.connection import BoundConnectionProvider, ConnectionFactory
from banking.infrastructure.database.transaction_manager import TransactionManager
from banking.infrastructure.repositories.postgres_account_repository import (
    PostgresAccountRepository,
)
from banking.infrastructure.repositories.postgres_customer_repository import (
    PostgresCustomerRepository,
)
from banking.infrastructure.repositories.postgres_transaction_repository import (
    PostgresTransactionRepository,
)

logger = logging.getLogger(__name__)


class PostgresUnitOfWork(UnitOfWork):
    """Unit of work for PostgreSQL: everything inside one `with` block is committed together or rolled back together."""

    def __init__(self, connection_factory: ConnectionFactory) -> None:
        """Store the factory; a connection is only opened when the `with` block is entered."""
        self._factory = connection_factory
        self._manager: TransactionManager | None = None
        self._committed = False

    def __enter__(self) -> Self:
        """Open a connection and expose repositories bound to it; nested use is rejected."""
        if self._manager is not None:
            raise RuntimeError(
                "UnitOfWork is not re-entrant; nested 'with' blocks are not supported."
            )
        conn = self._factory.create()
        self._manager = TransactionManager(conn)
        provider = BoundConnectionProvider(conn)
        self.customers = PostgresCustomerRepository(provider)
        self.accounts = PostgresAccountRepository(provider)
        self.transactions = PostgresTransactionRepository(provider)
        self._committed = False
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Roll back on error or when commit() was never called, then always close the connection."""
        manager = self._require_manager()
        try:
            if exc_type is not None:
                logger.warning("UnitOfWork rolled back due to %s", exc_type.__name__)
                manager.rollback()
            elif not self._committed:
                manager.rollback()
        finally:
            manager.close()
            self._manager = None

    def commit(self) -> None:
        """Commit all changes made inside the current `with` block."""
        self._require_manager().commit()
        self._committed = True

    def rollback(self) -> None:
        """Discard all changes made inside the current `with` block."""
        self._require_manager().rollback()

    def _require_manager(self) -> TransactionManager:
        """Return the active transaction manager or fail if used outside a `with` block."""
        if self._manager is None:
            raise RuntimeError("This operation is only allowed inside a 'with' block.")
        return self._manager
