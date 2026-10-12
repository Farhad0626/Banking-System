from typing import Any

from banking.application.ports.repositories.account_repository import AccountRepository
from banking.domain.entities.account import Account, AccountTerms
from banking.domain.enums.account_status import AccountStatus
from banking.domain.enums.account_type import AccountType
from banking.domain.exceptions.account_exceptions import AccountNotFoundException
from banking.domain.value_objects.account_number import AccountNumber
from banking.domain.value_objects.customer_id import CustomerId
from banking.domain.value_objects.money import Money
from banking.infrastructure.repositories.postgres_repository_base import PostgresRepositoryBase

_COLUMNS = (
    "id, account_number, customer_id, account_type, balance, status, interest_rate, "
    "overdraft_limit, term_start_date, term_end_date, created_at, updated_at, deleted_at"
)


def _to_account(row: dict[str, Any]) -> Account:
    """Map a database row to an Account entity."""
    return Account(
        id=row["id"],
        account_number=AccountNumber(row["account_number"]),
        customer_id=CustomerId(row["customer_id"]),
        account_type=AccountType(row["account_type"]),
        balance=Money(row["balance"]),
        account_status=AccountStatus(row["status"]),
        terms=AccountTerms(
            interest_rate=row["interest_rate"],
            overdraft_limit=row["overdraft_limit"],
            term_start_date=row["term_start_date"],
            term_end_date=row["term_end_date"],
        ),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        deleted_at=row["deleted_at"],
    )


class PostgresAccountRepository(PostgresRepositoryBase, AccountRepository):
    """Stores accounts in PostgreSQL and supports row locking (FOR UPDATE) for balance-changing operations."""

    def add(self, account: Account) -> Account:
        """Insert a new account and fill in its generated id and timestamps."""
        row = self._fetch_one(
            """
            INSERT INTO accounts
                (account_number, customer_id, account_type, balance, status,
                 interest_rate, overdraft_limit, term_start_date, term_end_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, created_at, updated_at
            """,
            (
                account.account_number.value,
                account.customer_id.value,
                account.account_type.value,
                account.balance.amount,
                account.account_status.value,
                account.terms.interest_rate,
                account.terms.overdraft_limit,
                account.terms.term_start_date,
                account.terms.term_end_date,
            ),
        )
        if row is None:
            raise RuntimeError("Account insert returned no row.")
        account.id = row["id"]
        account.created_at = row["created_at"]
        account.updated_at = row["updated_at"]
        return account

    def get_by_id(self, account_id: int, for_update: bool = False) -> Account | None:
        """Return an account by id; with for_update=True the row stays locked until the transaction ends."""
        sql = f"SELECT {_COLUMNS} FROM accounts WHERE id = %s AND deleted_at IS NULL"
        if for_update:
            sql += " FOR UPDATE"
        row = self._fetch_one(sql, (account_id,))
        return _to_account(row) if row else None

    def get_by_account_number(self, account_number: str) -> Account | None:
        """Return an account by its account number, or None."""
        row = self._fetch_one(
            f"SELECT {_COLUMNS} FROM accounts WHERE account_number = %s AND deleted_at IS NULL",
            (account_number,),
        )
        return _to_account(row) if row else None

    def get_by_number(self, account_number: str) -> Account | None:
        """Backward-compatible alias for get_by_account_number."""
        return self.get_by_account_number(account_number)

    def get_by_customer_id(self, customer_id: int) -> list[Account]:
        """Return all non-deleted accounts owned by a customer."""
        rows = self._fetch_all(
            f"SELECT {_COLUMNS} FROM accounts WHERE customer_id = %s AND deleted_at IS NULL ORDER BY id",
            (customer_id,),
        )
        return [_to_account(row) for row in rows]

    def update(self, account: Account) -> None:
        """Persist changes to an existing account; raises AccountNotFound if the row does not exist."""
        if account.id is None:
            raise AccountNotFoundException("Account without an ID cannot be updated.")
        affected = self._execute(
            """
            UPDATE accounts
               SET balance = %s, status = %s, interest_rate = %s, overdraft_limit = %s,
                   term_start_date = %s, term_end_date = %s, deleted_at = %s
             WHERE id = %s
            """,
            (
                account.balance.amount,
                account.account_status.value,
                account.terms.interest_rate,
                account.terms.overdraft_limit,
                account.terms.term_start_date,
                account.terms.term_end_date,
                account.deleted_at,
                account.id,
            ),
        )
        if affected == 0:
            raise AccountNotFoundException(f"Account with ID {account.id} was not found.")

    def search(self, account_type: str | None = None, status: str | None = None) -> list[Account]:
        """List non-deleted accounts, optionally filtered by type and status (filtering happens in SQL)."""
        conditions, params = ["deleted_at IS NULL"], []
        if account_type:
            conditions.append("account_type = %s")
            params.append(account_type)
        if status:
            conditions.append("status = %s")
            params.append(status)
        rows = self._fetch_all(
            f"SELECT {_COLUMNS} FROM accounts WHERE {' AND '.join(conditions)} ORDER BY id", params
        )
        return [_to_account(row) for row in rows]

    def delete(self, account_id: int) -> None:
        """Soft-delete an account so transaction history remains available."""
        affected = self._execute(
            "UPDATE accounts SET deleted_at = now() WHERE id = %s AND deleted_at IS NULL",
            (account_id,),
        )
        if affected == 0:
            raise AccountNotFoundException(f"Account with ID {account_id} was not found.")
