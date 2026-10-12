from datetime import datetime
from typing import Any

from banking.application.ports.repositories.transaction_repository import TransactionRepository
from banking.domain.entities.transaction import Transaction
from banking.domain.enums.transaction_status import TransactionStatus
from banking.domain.enums.transaction_type import TransactionType
from banking.domain.value_objects.money import Money
from banking.infrastructure.repositories.postgres_repository_base import PostgresRepositoryBase

_COLUMNS = (
    "id, transaction_type, amount, source_account_id, destination_account_id, status, created_at"
)


def _to_transaction(row: dict[str, Any]) -> Transaction:
    """Map a database row to a Transaction entity."""
    return Transaction(
        id=int(row["id"]),
        transaction_type=TransactionType(row["transaction_type"]),
        amount=Money(row["amount"]),
        source_account_id=row["source_account_id"],
        destination_account_id=row["destination_account_id"],
        status=TransactionStatus(row["status"]),
        created_at=row["created_at"],
    )


class PostgresTransactionRepository(PostgresRepositoryBase, TransactionRepository):
    """Append-only ledger of transactions in PostgreSQL with all filtering done in SQL."""

    def add(self, transaction: Transaction) -> Transaction:
        """Insert a transaction and fill in its generated id and timestamp."""
        row = self._fetch_one(
            """
            INSERT INTO transactions
                (transaction_type, amount, source_account_id, destination_account_id, status)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, created_at
            """,
            (
                transaction.transaction_type.value,
                transaction.amount.amount,
                transaction.source_account_id,
                transaction.destination_account_id,
                transaction.status.value,
            ),
        )
        if row is None:
            raise RuntimeError("Transaction insert returned no row.")
        transaction.id = row["id"]
        transaction.created_at = row["created_at"]
        return transaction

    def get_by_id(self, transaction_id: int) -> Transaction | None:
        """Return a transaction by id, or None."""
        row = self._fetch_one(
            f"SELECT {_COLUMNS} FROM transactions WHERE id = %s", (transaction_id,)
        )
        return _to_transaction(row) if row else None

    def get_by_account_id(self, account_id: int) -> list[Transaction]:
        """Return all transactions where the account is source or destination, newest first."""
        rows = self._fetch_all(
            f"""
            SELECT {_COLUMNS} FROM transactions
            WHERE source_account_id = %s OR destination_account_id = %s
            ORDER BY created_at DESC, id DESC
            """,
            (account_id, account_id),
        )
        return [_to_transaction(row) for row in rows]

    def search(
        self,
        account_id: int | None = None,
        transaction_type: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[Transaction]:
        """Search transactions by account, type and date range using a SQL WHERE clause."""
        conditions: list[str] = []
        params: list[Any] = []
        if account_id is not None:
            conditions.append("(source_account_id = %s OR destination_account_id = %s)")
            params += [account_id, account_id]
        if transaction_type:
            conditions.append("transaction_type = %s")
            params.append(transaction_type)
        if date_from is not None:
            conditions.append("created_at >= %s")
            params.append(date_from)
        if date_to is not None:
            conditions.append("created_at <= %s")
            params.append(date_to)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        rows = self._fetch_all(
            f"SELECT {_COLUMNS} FROM transactions {where} ORDER BY created_at DESC, id DESC", params
        )
        return [_to_transaction(row) for row in rows]
