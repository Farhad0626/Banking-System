from contextlib import contextmanager
from datetime import UTC
from types import SimpleNamespace

import psycopg
import pytest

from banking.domain.exceptions.account_exceptions import AccountNotFoundException
from banking.domain.exceptions.customer_exceptions import CustomerNotFoundException
from banking.domain.value_objects.customer_id import CustomerId
from banking.domain.value_objects.phone_number import PhoneNumber
from banking.infrastructure.database import postgres_unit_of_work as postgres_uow_module
from banking.infrastructure.database.connection import (
    BoundConnectionProvider,
    ConnectionFactory,
    PerCallConnectionProvider,
)
from banking.infrastructure.database.postgres_unit_of_work import PostgresUnitOfWork
from banking.infrastructure.database.transaction_manager import TransactionManager
from banking.infrastructure.repositories import (
    postgres_account_repository,
    postgres_customer_repository,
    postgres_transaction_repository,
)
from banking.infrastructure.repositories.postgres_account_repository import (
    PostgresAccountRepository,
)
from banking.infrastructure.repositories.postgres_card_repository import PostgresCardRepository
from banking.infrastructure.repositories.postgres_customer_repository import (
    PostgresCustomerRepository,
)
from banking.infrastructure.repositories.postgres_repository_base import PostgresRepositoryBase
from banking.infrastructure.repositories.postgres_transaction_repository import (
    PostgresTransactionRepository,
)


class FakeResult:
    def __init__(self, one=None, many=None, rowcount=1):
        self.one = one
        self.many = [] if many is None else many
        self.rowcount = rowcount

    def fetchone(self):
        return self.one

    def fetchall(self):
        return self.many


class FakeConnection:
    def __init__(self):
        self.calls = []
        self.result = FakeResult()
        self.closed = False
        self.commits = 0
        self.rollbacks = 0
        self.closes = 0

    def execute(self, sql, params=()):
        self.calls.append((sql, tuple(params)))
        return self.result

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closes += 1
        self.closed = True


class FakeProvider:
    def __init__(self, connection):
        self.conn = connection

    @contextmanager
    def connection(self):
        yield self.conn


class FakeFactory:
    def __init__(self, connection):
        self.conn = connection
        self.calls = 0

    def create(self):
        self.calls += 1
        return self.conn


class ConcreteAccountRepositoryForTest(PostgresAccountRepository):
    def get_by_account_number(self, account_number):
        return None

    def delete(self, account_id):
        return None


class ConcreteCustomerRepositoryForTest(PostgresCustomerRepository):
    def delete(self, customer_id):
        return None


class RepositoryProbe:
    def __init__(self, provider):
        self.provider = provider


def make_test_uow(monkeypatch, conn):
    monkeypatch.setattr(postgres_uow_module, "PostgresCustomerRepository", RepositoryProbe)
    monkeypatch.setattr(postgres_uow_module, "PostgresAccountRepository", RepositoryProbe)
    monkeypatch.setattr(postgres_uow_module, "PostgresTransactionRepository", RepositoryProbe)
    return PostgresUnitOfWork(FakeFactory(conn))


def test_connection_factory_uses_config_and_sets_read_committed(monkeypatch):
    config = SimpleNamespace(
        get_str=lambda key, default=None: {
            "DB_HOST": "db",
            "DB_NAME": "bank",
            "DB_USER": "user",
            "DB_PASSWORD": "password",
        }[key],
        get_int=lambda key, default=None: 5544,
    )
    factory = ConnectionFactory.from_configuration(config)
    conn = FakeConnection()
    connect_calls = []

    def connect(**kwargs):
        connect_calls.append(kwargs)
        return conn

    monkeypatch.setattr("banking.infrastructure.database.connection.psycopg.connect", connect)

    result = factory.create()

    assert result is conn
    assert factory.dbname == "bank"
    assert connect_calls[0]["host"] == "db"
    assert connect_calls[0]["port"] == 5544
    assert connect_calls[0]["dbname"] == "bank"
    assert connect_calls[0]["user"] == "user"
    assert connect_calls[0]["password"] == "password"
    assert connect_calls[0]["options"] == "-c timezone=UTC"
    assert connect_calls[0]["row_factory"] is not None
    assert conn.isolation_level == psycopg.IsolationLevel.READ_COMMITTED


def test_per_call_provider_uses_connection_context_manager():
    class ContextFactory:
        @contextmanager
        def create(self):
            yield "connection"

    with PerCallConnectionProvider(ContextFactory()).connection() as conn:
        assert conn == "connection"


def test_bound_provider_yields_same_connection_without_owning_lifecycle():
    conn = FakeConnection()

    with BoundConnectionProvider(conn).connection() as yielded:
        assert yielded is conn

    assert conn.closes == 0


def test_transaction_manager_delegates_transaction_methods_and_closes_once():
    conn = FakeConnection()
    manager = TransactionManager(conn)

    manager.commit()
    manager.rollback()
    manager.close()
    manager.close()

    assert conn.commits == 1
    assert conn.rollbacks == 1
    assert conn.closes == 1


def test_unit_of_work_commits_and_closes_on_success(monkeypatch):
    conn = FakeConnection()
    uow = make_test_uow(monkeypatch, conn)

    with uow as active:
        assert active is uow
        assert active.customers.provider._conn is conn
        assert active.accounts.provider._conn is conn
        assert active.transactions.provider._conn is conn
        active.commit()

    assert conn.commits == 1
    assert conn.rollbacks == 0
    assert conn.closes == 1


def test_unit_of_work_rolls_back_without_commit_and_on_exception(monkeypatch):
    conn = FakeConnection()
    uow = make_test_uow(monkeypatch, conn)
    with uow:
        pass

    assert conn.rollbacks == 1

    conn2 = FakeConnection()
    uow2 = make_test_uow(monkeypatch, conn2)
    with pytest.raises(RuntimeError, match="failure"), uow2:
        raise RuntimeError("failure")

    assert conn2.rollbacks == 1
    assert conn2.closes == 1


def test_unit_of_work_rejects_nested_entry_and_operations_outside_context(monkeypatch):
    uow = make_test_uow(monkeypatch, FakeConnection())

    with pytest.raises(RuntimeError, match="inside a 'with' block"):
        uow.commit()

    with uow, pytest.raises(RuntimeError, match="not re-entrant"):
        uow.__enter__()


def test_repository_base_executes_and_returns_database_results():
    conn = FakeConnection()
    conn.result = FakeResult(one={"id": 7}, many=[{"id": 7}], rowcount=1)
    repository = PostgresRepositoryBase(FakeProvider(conn))

    assert repository._fetch_one("SELECT %s", (7,)) == {"id": 7}
    assert repository._fetch_all("SELECT %s", (7,)) == [{"id": 7}]
    assert repository._execute("UPDATE", (7,)) == 1
    assert [params for _, params in conn.calls] == [(7,), (7,), (7,)]


def test_account_repository_uses_optional_row_lock_and_filters_search(monkeypatch):
    marker = object()
    row = {"id": 1}
    conn = FakeConnection()
    conn.result = FakeResult(one=row, many=[row])
    repository = ConcreteAccountRepositoryForTest(FakeProvider(conn))
    monkeypatch.setattr(postgres_account_repository, "_to_account", lambda found: marker)

    assert repository.get_by_id(1, for_update=True) is marker
    sql, params = conn.calls[-1]
    assert "FOR UPDATE" in sql
    assert params == (1,)
    assert repository.search(account_type="SAVINGS", status="ACTIVE") == [marker]
    sql, params = conn.calls[-1]
    assert "account_type = %s" in sql and "status = %s" in sql
    assert params == ("SAVINGS", "ACTIVE")


def test_account_repository_update_raises_when_no_row_is_updated():
    conn = FakeConnection()
    conn.result = FakeResult(rowcount=0)
    repository = ConcreteAccountRepositoryForTest(FakeProvider(conn))
    account = SimpleNamespace(
        balance=SimpleNamespace(amount=10),
        account_status=SimpleNamespace(value="ACTIVE"),
        terms=SimpleNamespace(
            interest_rate=0,
            overdraft_limit=0,
            term_start_date=None,
            term_end_date=None,
        ),
        deleted_at=None,
        id=99,
    )

    with pytest.raises(AccountNotFoundException, match="ID 99"):
        repository.update(account)


def test_customer_repository_escapes_like_metacharacters_and_uses_bound_parameters(monkeypatch):
    conn = FakeConnection()
    row = {"id": 2}
    conn.result = FakeResult(many=[row])
    repository = ConcreteCustomerRepositoryForTest(FakeProvider(conn))
    marker = object()
    monkeypatch.setattr(postgres_customer_repository, "_to_customer", lambda found: marker)

    assert repository.search(r"a%_\\b") == [marker]
    sql, params = conn.calls[-1]
    assert "ILIKE %s" in sql
    assert params == (r"%a\%\_\\\\b%",) * 5


def test_customer_repository_update_raises_when_customer_is_missing():
    conn = FakeConnection()
    conn.result = FakeResult(rowcount=0)
    repository = ConcreteCustomerRepositoryForTest(FakeProvider(conn))
    customer = SimpleNamespace(
        first_name="A",
        last_name="B",
        mobile=PhoneNumber("09120000000"),
        email="a@example.test",
        password_hash="hash",
        is_active=True,
        is_restricted=False,
        deleted_at=None,
        id=CustomerId(404),
    )

    with pytest.raises(CustomerNotFoundException, match="ID 404"):
        repository.update(customer)


def test_transaction_repository_search_combines_all_filters(monkeypatch):
    conn = FakeConnection()
    row = {"id": 3}
    conn.result = FakeResult(many=[row])
    repository = PostgresTransactionRepository(FakeProvider(conn))
    marker = object()
    monkeypatch.setattr(postgres_transaction_repository, "_to_transaction", lambda found: marker)

    from datetime import datetime

    start = datetime(2025, 1, 1, tzinfo=UTC)
    end = datetime(2025, 1, 31, tzinfo=UTC)
    assert repository.search(7, "TRANSFER", start, end) == [marker]

    sql, params = conn.calls[-1]
    assert "(source_account_id = %s OR destination_account_id = %s)" in sql
    assert "transaction_type = %s" in sql
    assert "created_at >= %s" in sql and "created_at <= %s" in sql
    assert params == (7, 7, "TRANSFER", start, end)


def test_transaction_repository_search_without_filters_has_no_where_clause():
    conn = FakeConnection()
    conn.result = FakeResult(many=[])
    repository = PostgresTransactionRepository(FakeProvider(conn))

    assert repository.search() == []
    sql, params = conn.calls[-1]
    assert " WHERE " not in sql
    assert params == ()


def test_card_repository_explicitly_reports_unimplemented_core_release():
    with pytest.raises(NotImplementedError, match="outside the Core Release"):
        PostgresCardRepository().add(object())
