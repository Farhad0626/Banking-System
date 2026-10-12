import os
from pathlib import Path

import psycopg
import pytest
from dotenv import load_dotenv
from psycopg.rows import dict_row

from banking.config.settings import get_db_config
from banking.infrastructure.database.connection import (
    BoundConnectionProvider,
    ConnectionFactory,
)
from banking.infrastructure.repositories.postgres_account_repository import (
    PostgresAccountRepository,
)
from banking.infrastructure.repositories.postgres_customer_repository import (
    PostgresCustomerRepository,
)
from banking.infrastructure.repositories.postgres_transaction_repository import (
    PostgresTransactionRepository,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = PROJECT_ROOT / "database" / "migrations"


@pytest.fixture(scope="session")
def postgres_factory() -> ConnectionFactory:
    load_dotenv(PROJECT_ROOT / ".env")
    test_db_name = os.getenv("TEST_DB_NAME")
    if not test_db_name:
        pytest.skip("Set TEST_DB_NAME to enable PostgreSQL integration tests.")
    if not test_db_name.endswith("_test"):
        pytest.fail("TEST_DB_NAME must end with '_test' to protect non-test databases.")

    db_config = get_db_config()
    if test_db_name == db_config["dbname"]:
        pytest.fail("TEST_DB_NAME must be different from DB_NAME.")

    factory = ConnectionFactory(
        host=db_config["host"],
        port=db_config["port"],
        dbname=test_db_name,
        user=db_config["user"],
        password=db_config["password"],
    )
    try:
        connection = psycopg.connect(
            host=db_config["host"],
            port=db_config["port"],
            dbname=test_db_name,
            user=db_config["user"],
            password=db_config["password"],
            connect_timeout=3,
            row_factory=dict_row,
            options="-c timezone=UTC",
        )
    except psycopg.OperationalError as exc:
        pytest.skip(
            f"PostgreSQL test database '{test_db_name}' is unavailable ({type(exc).__name__})."
        )

    try:
        migrations = sorted(MIGRATIONS_DIR.glob("*.sql"))
        for _ in range(2):
            for migration in migrations:
                connection.execute(migration.read_text(encoding="utf-8"), prepare=False)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    return factory


@pytest.fixture
def db_connection(postgres_factory: ConnectionFactory):
    connection = postgres_factory.create()
    try:
        yield connection
    finally:
        connection.rollback()
        connection.close()


@pytest.fixture
def repositories(db_connection: psycopg.Connection):
    provider = BoundConnectionProvider(db_connection)
    return {
        "customers": PostgresCustomerRepository(provider),
        "accounts": PostgresAccountRepository(provider),
        "transactions": PostgresTransactionRepository(provider),
    }
