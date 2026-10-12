from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from banking.application.context.session_context import Session
from banking.application.dto.account.account_dto import CreateAccountRequest
from banking.application.use_cases.account.activate_account import ActivateAccount
from banking.application.use_cases.account.apply_interest import ApplyInterest
from banking.application.use_cases.account.create_account import CreateAccount
from banking.application.use_cases.account.deactivate_account import DeactivateAccount
from banking.application.use_cases.account.get_account import GetAccount
from banking.domain.enums.account_type import AccountType
from banking.domain.exceptions.account_exceptions import AccountNotFoundException
from banking.domain.exceptions.auth_exceptions import AuthenticationFailedException
from banking.domain.exceptions.customer_exceptions import CustomerNotFoundException
from banking.domain.value_objects.customer_id import CustomerId
from banking.domain.value_objects.money import Money


def session(customer_id: int = 8) -> Session:
    return Session(customer_id, "CUSTOMER", datetime.now(UTC))


def account(*, customer_id: int = 8, balance: str = "12.00") -> SimpleNamespace:
    return SimpleNamespace(
        id=41,
        customer_id=CustomerId(customer_id),
        account_number=SimpleNamespace(value="1234567890123456"),
        account_type=AccountType.SAVINGS,
        account_status=SimpleNamespace(value="ACTIVE"),
        balance=Money(Decimal(balance)),
        is_deleted=False,
        activate=Mock(),
        deactivate=Mock(),
        deposit=Mock(),
    )


def test_activate_account_updates_existing_account() -> None:
    existing = account()
    repository = Mock()
    repository.get_by_id.return_value = existing

    ActivateAccount(repository).execute(41)

    repository.get_by_id.assert_called_once_with(41)
    existing.activate.assert_called_once_with()
    repository.update.assert_called_once_with(existing)


def test_activate_account_raises_when_account_is_missing() -> None:
    repository = Mock()
    repository.get_by_id.return_value = None

    with pytest.raises(AccountNotFoundException):
        ActivateAccount(repository).execute(41)

    repository.update.assert_not_called()


def test_deactivate_account_updates_existing_account() -> None:
    existing = account()
    repository = Mock()
    repository.get_by_id.return_value = existing

    DeactivateAccount(repository).execute(41)

    existing.deactivate.assert_called_once_with()
    repository.update.assert_called_once_with(existing)


def test_get_account_denies_non_owner_before_building_view() -> None:
    repository = Mock()
    repository.get_by_id.return_value = account(customer_id=8)
    session = SimpleNamespace(is_owner=Mock(return_value=False))

    with pytest.raises(AuthenticationFailedException):
        GetAccount(repository).execute(41, session)

    session.is_owner.assert_called_once_with(8)


def test_get_account_raises_for_deleted_or_missing_account() -> None:
    repository = Mock()
    repository.get_by_id.return_value = None
    session = SimpleNamespace(is_owner=Mock(return_value=True))

    with pytest.raises(AccountNotFoundException):
        GetAccount(repository).execute(41, session)
    session.is_owner.assert_not_called()

    deleted = account()
    deleted.is_deleted = True
    repository.get_by_id.return_value = deleted
    with pytest.raises(AccountNotFoundException):
        GetAccount(repository).execute(41, session)


def test_get_account_returns_view_for_owned_account() -> None:
    repository = Mock()
    repository.get_by_id.return_value = account()
    session = SimpleNamespace(is_owner=Mock(return_value=True))

    result = GetAccount(repository).execute(41, session)

    assert result.account_id == 41
    assert result.customer_id == 8
    assert result.account_number == "1234567890123456"
    assert result.account_type == "SAVINGS"
    assert result.balance == "12.00"
    assert result.status == "ACTIVE"
    repository.get_by_id.assert_called_once_with(41)


def test_apply_interest_deposits_and_persists_positive_interest() -> None:
    existing = account()
    repository = Mock()
    repository.get_by_id.return_value = existing
    calculator = Mock()
    calculator.calculate_interest.return_value = Money(Decimal("1.25"))

    result = ApplyInterest(repository, calculator).execute(41)

    assert result == "1.25"
    calculator.calculate_interest.assert_called_once_with(existing)
    existing.deposit.assert_called_once_with(Money(Decimal("1.25")))
    repository.update.assert_called_once_with(existing)


def test_apply_interest_does_not_persist_zero_or_negative_interest() -> None:
    existing = account()
    repository = Mock()
    repository.get_by_id.return_value = existing
    calculator = Mock()
    calculator.calculate_interest.return_value = Money.zero()

    assert ApplyInterest(repository, calculator).execute(41) == "0.00"
    existing.deposit.assert_not_called()
    repository.update.assert_not_called()

    calculator.calculate_interest.return_value = Money(Decimal("-0.25"))
    assert ApplyInterest(repository, calculator).execute(41) == "-0.25"
    existing.deposit.assert_not_called()
    repository.update.assert_not_called()


def test_apply_interest_raises_for_missing_account() -> None:
    repository = Mock()
    repository.get_by_id.return_value = None
    calculator = Mock()

    with pytest.raises(AccountNotFoundException):
        ApplyInterest(repository, calculator).execute(41)
    calculator.calculate_interest.assert_not_called()


def test_create_account_rejects_missing_or_deleted_customer() -> None:
    customers = Mock()
    accounts = Mock()
    generator = Mock()
    config = Mock()
    customers.get_by_id.return_value = None
    use_case = CreateAccount(customers, accounts, generator, config)

    with pytest.raises(CustomerNotFoundException):
        use_case.execute(CreateAccountRequest(8, "SAVINGS"), session())
    generator.generate.assert_not_called()
    accounts.add.assert_not_called()

    customers.get_by_id.return_value = SimpleNamespace(id=CustomerId(8), is_deleted=True)
    with pytest.raises(CustomerNotFoundException):
        use_case.execute(CreateAccountRequest(8, "SAVINGS"), session())


@pytest.mark.parametrize("deposit", ["not-money", "-1"])
def test_create_account_rejects_invalid_or_negative_opening_deposit(deposit: str) -> None:
    customers = Mock()
    customers.get_by_id.return_value = SimpleNamespace(id=CustomerId(8), is_deleted=False)
    accounts = Mock()
    use_case = CreateAccount(customers, accounts, Mock(), Mock())

    with pytest.raises(ValueError):
        use_case.execute(CreateAccountRequest(8, "SAVINGS", deposit), session())
    accounts.add.assert_not_called()


def test_create_account_builds_terms_retries_number_and_returns_saved_view() -> None:
    customers = Mock()
    customers.get_by_id.return_value = SimpleNamespace(id=CustomerId(8), is_deleted=False)
    accounts = Mock()
    accounts.get_by_account_number.side_effect = [account(), None]
    generator = Mock()
    generator.generate.side_effect = ["1111111111111111", "2222222222222222"]
    config = Mock()
    config.get_decimal.return_value = Decimal("0.03")
    accounts.add.side_effect = lambda created: created
    use_case = CreateAccount(customers, accounts, generator, config)

    result = use_case.execute(CreateAccountRequest(8, "SAVINGS", "25.00"), session())

    assert generator.generate.call_count == 2
    assert accounts.get_by_account_number.call_count == 2
    saved = accounts.add.call_args.args[0]
    assert saved.customer_id == CustomerId(8)
    assert saved.account_type is AccountType.SAVINGS
    assert saved.balance == Money(Decimal("25.00"))
    assert saved.terms.interest_rate == Decimal("0.03")
    config.get_decimal.assert_called_once_with("SAVINGS_INTEREST_RATE")
    assert result.account_id == saved.id


def test_create_account_fails_after_bounded_unique_number_attempts() -> None:
    customers = Mock()
    customers.get_by_id.return_value = SimpleNamespace(id=8, is_deleted=False)
    accounts = Mock()
    accounts.get_by_account_number.return_value = account()
    generator = Mock()
    generator.generate.return_value = "1111111111111111"
    use_case = CreateAccount(customers, accounts, generator, Mock())

    with pytest.raises(RuntimeError, match="unique account number"):
        use_case.execute(CreateAccountRequest(8, "CHECKING"), session())
    assert generator.generate.call_count == 5
    accounts.add.assert_not_called()
