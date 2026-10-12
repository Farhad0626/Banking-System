from abc import ABC, abstractmethod
from collections.abc import Iterator
from contextlib import AbstractContextManager, contextmanager
from typing import Any, TypedDict

import psycopg
from psycopg.rows import dict_row

from banking.application.ports.configuration.configuration_service import ConfigurationService


class ConnectionParameters(TypedDict):
    host: str
    port: int
    dbname: str
    user: str
    password: str


class ConnectionFactory:
    """Creates PostgreSQL connections with fixed parameters and READ COMMITTED isolation."""

    def __init__(self, host: str, port: int, dbname: str, user: str, password: str) -> None:
        """Store connection parameters; no connection is opened until create() is called."""
        self._params: ConnectionParameters = {
            "host": host,
            "port": port,
            "dbname": dbname,
            "user": user,
            "password": password,
        }

    @classmethod
    def from_configuration(cls, config: ConfigurationService) -> ConnectionFactory:
        """Build a factory from the DB_* settings of a ConfigurationService."""
        return cls(
            host=config.get_str("DB_HOST", "localhost"),
            port=config.get_int("DB_PORT", 5432),
            dbname=config.get_str("DB_NAME"),
            user=config.get_str("DB_USER"),
            password=config.get_str("DB_PASSWORD"),
        )

    @property
    def dbname(self) -> str:
        """Name of the target database."""
        return self._params["dbname"]

    def create(self) -> psycopg.Connection[dict[str, Any]]:
        """Open a new connection that returns rows as dicts and uses UTC timestamps."""
        conn = psycopg.connect(**self._params, row_factory=dict_row, options="-c timezone=UTC")
        conn.isolation_level = psycopg.IsolationLevel.READ_COMMITTED
        return conn


class ConnectionProvider(ABC):
    """Abstract way for repositories to get a connection without knowing whether a UnitOfWork is active."""

    @abstractmethod
    def connection(self) -> AbstractContextManager[psycopg.Connection[dict[str, Any]]]:
        """Yield a connection to run statements on."""


class PerCallConnectionProvider(ConnectionProvider):
    """Standalone operations: one connection per call, committed on success, rolled back on error, then closed."""

    def __init__(self, factory: ConnectionFactory) -> None:
        """Keep the factory used to open a fresh connection for every call."""
        self._factory = factory

    @contextmanager
    def connection(self) -> Iterator[psycopg.Connection[dict[str, Any]]]:
        """Open a connection; psycopg commits on clean exit, rolls back on exception, and closes it."""
        with self._factory.create() as conn:
            yield conn


class BoundConnectionProvider(ConnectionProvider):
    """Inside a UnitOfWork: every repository shares one connection whose commit/rollback the UoW controls."""

    def __init__(self, conn: psycopg.Connection[dict[str, Any]]) -> None:
        """Bind the provider to an already-open connection."""
        self._conn = conn

    @contextmanager
    def connection(self) -> Iterator[psycopg.Connection[dict[str, Any]]]:
        """Yield the shared connection without committing or closing it."""
        yield self._conn
