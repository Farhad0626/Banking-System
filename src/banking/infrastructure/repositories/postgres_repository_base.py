from collections.abc import Sequence
from typing import Any

from banking.infrastructure.database.connection import ConnectionProvider


class PostgresRepositoryBase:
    """Base class providing parameterized SQL execution helpers on top of a ConnectionProvider."""

    def __init__(self, connection_provider: ConnectionProvider) -> None:
        """Store the provider used to obtain connections."""
        self._provider = connection_provider

    def _fetch_one(self, sql: str, params: Sequence[Any] = ()) -> dict[str, Any] | None:
        """Run a query and return the first row as a dict, or None."""
        with self._provider.connection() as connection:
            return connection.execute(sql, params).fetchone()

    def _fetch_all(self, sql: str, params: Sequence[Any] = ()) -> list[dict[str, Any]]:
        """Run a query and return all rows as dicts."""
        with self._provider.connection() as connection:
            return connection.execute(sql, params).fetchall()

    def _execute(self, sql: str, params: Sequence[Any] = ()) -> int:
        """Run a statement and return the number of affected rows."""
        with self._provider.connection() as connection:
            return connection.execute(sql, params).rowcount
