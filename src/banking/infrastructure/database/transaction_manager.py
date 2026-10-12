from typing import Any

import psycopg


class TransactionManager:
    """Owns commit, rollback and close for one connection (psycopg opens the transaction implicitly)."""

    def __init__(self, connection: psycopg.Connection[dict[str, Any]]) -> None:
        """Wrap the connection whose transaction lifecycle is being managed."""
        self._conn = connection

    def commit(self) -> None:
        """Commit the current transaction."""
        self._conn.commit()

    def rollback(self) -> None:
        """Roll back the current transaction."""
        self._conn.rollback()

    def close(self) -> None:
        """Close the connection if it is still open."""
        if not self._conn.closed:
            self._conn.close()
