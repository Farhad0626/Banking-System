from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from banking.application.context.session_context import Session
from banking.application.use_cases.customer.activate_customer import ActivateCustomer
from banking.application.use_cases.customer.delete_customer import DeleteCustomer
from banking.application.use_cases.customer.get_customer import GetCustomer
from banking.application.use_cases.customer.restrict_customer import RestrictCustomer
from banking.domain.exceptions.auth_exceptions import AuthenticationFailedException
from banking.domain.exceptions.customer_exceptions import CustomerNotFoundException
from banking.domain.value_objects.customer_id import CustomerId


def customer(*, deleted: bool = False) -> SimpleNamespace:
    return SimpleNamespace(
        id=CustomerId(12),
        first_name="Ada",
        last_name="Lovelace",
        national_id=SimpleNamespace(value="1234567890"),
        mobile=SimpleNamespace(value="09120000000"),
        email="ada@example.test",
        username="ada",
        is_active=True,
        is_restricted=False,
        is_deleted=deleted,
        activate=Mock(),
        restrict=Mock(),
        mark_deleted=Mock(),
    )


def session(customer_id: int = 12) -> Session:
    from datetime import UTC, datetime

    return Session(customer_id, "CUSTOMER", datetime.now(UTC))


@pytest.mark.parametrize("use_case", [ActivateCustomer, RestrictCustomer])
def test_customer_state_actions_mutate_and_update(use_case: type) -> None:
    existing = customer()
    repository = Mock()
    repository.get_by_id.return_value = existing

    use_case(repository).execute(12)

    getattr(
        existing, "activate" if use_case is ActivateCustomer else "restrict"
    ).assert_called_once()
    repository.update.assert_called_once_with(existing)


@pytest.mark.parametrize("use_case", [ActivateCustomer, RestrictCustomer])
@pytest.mark.parametrize("missing", [True, False])
def test_customer_state_actions_reject_missing_or_deleted_customers(
    use_case: type, missing: bool
) -> None:
    repository = Mock()
    repository.get_by_id.return_value = None if missing else customer(deleted=True)

    with pytest.raises(CustomerNotFoundException):
        use_case(repository).execute(12)
    repository.update.assert_not_called()


def test_get_customer_checks_ownership_before_repository_lookup() -> None:
    repository = Mock()
    denied = SimpleNamespace(is_owner=Mock(return_value=False))

    with pytest.raises(AuthenticationFailedException):
        GetCustomer(repository).execute(12, denied)

    denied.is_owner.assert_called_once_with(12)
    repository.get_by_id.assert_not_called()


def test_get_customer_rejects_missing_or_deleted_customer() -> None:
    repository = Mock()
    repository.get_by_id.return_value = None
    with pytest.raises(CustomerNotFoundException):
        GetCustomer(repository).execute(12, session())

    deleted = customer(deleted=True)
    repository.get_by_id.return_value = deleted
    with pytest.raises(CustomerNotFoundException):
        GetCustomer(repository).execute(12, session())


def test_get_customer_returns_owner_view() -> None:
    repository = Mock()
    repository.get_by_id.return_value = customer()

    result = GetCustomer(repository).execute(12, session())

    assert result.customer_id == 12
    assert result.first_name == "Ada"
    assert result.last_name == "Lovelace"
    assert result.national_id == "1234567890"
    assert result.mobile == "09120000000"
    assert result.email == "ada@example.test"
    assert result.username == "ada"
    assert result.is_active
    assert not result.is_restricted


class UnitOfWorkFake:
    def __init__(self, customer_record, accounts):
        self.customers = Mock()
        self.customers.get_by_id.return_value = customer_record
        self.accounts = Mock()
        self.accounts.get_by_customer_id.return_value = accounts
        self.commit = Mock()
        self.rollback = Mock()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return None


def test_delete_customer_soft_deletes_customer_and_deactivates_accounts() -> None:
    existing = customer()
    first = SimpleNamespace(deactivate=Mock())
    second = SimpleNamespace(deactivate=Mock())
    uow = UnitOfWorkFake(existing, [first, second])

    DeleteCustomer(uow).execute(12)

    existing.mark_deleted.assert_called_once_with()
    uow.customers.update.assert_called_once_with(existing)
    uow.accounts.get_by_customer_id.assert_called_once_with(12)
    for account in (first, second):
        account.deactivate.assert_called_once_with()
        uow.accounts.update.assert_any_call(account)
    uow.commit.assert_called_once_with()
    uow.rollback.assert_not_called()


def test_delete_customer_missing_record_does_not_commit() -> None:
    uow = UnitOfWorkFake(None, [])

    with pytest.raises(CustomerNotFoundException):
        DeleteCustomer(uow).execute(12)

    uow.commit.assert_not_called()
    uow.customers.update.assert_not_called()
