from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from banking.domain.entities.account import Account, AccountTerms
from banking.domain.enums.account_status import AccountStatus
from banking.domain.enums.account_type import AccountType
from banking.domain.exceptions.account_exceptions import AccountInactiveException
from banking.domain.exceptions.insufficient_balance import InsufficientBalanceException
from banking.domain.exceptions.transaction_exceptions import InvalidAmountException
from banking.domain.value_objects.account_number import AccountNumber
from banking.domain.value_objects.customer_id import CustomerId
from banking.domain.value_objects.money import Money


def make_account(
    *,
    balance: str = "100.00",
    account_type: AccountType = AccountType.SAVINGS,
    status: AccountStatus = AccountStatus.ACTIVE,
    terms: AccountTerms | None = None,
) -> Account:
    return Account(
        id=1,
        account_number=AccountNumber("1234567890123456"),
        customer_id=CustomerId(1),
        account_type=account_type,
        account_status=status,
        balance=Money.of(balance),
        terms=terms or AccountTerms(),
    )


def test_account_deleted_property_reflects_deleted_timestamp() -> None:
    account = make_account()

    assert not account.is_deleted
    account.deleted_at = datetime(2026, 1, 1, tzinfo=UTC)
    assert account.is_deleted


def test_ensure_active_accepts_active_and_rejects_other_states() -> None:
    make_account().ensure_active()

    for status in (AccountStatus.INACTIVE, AccountStatus.DELETED):
        with pytest.raises(AccountInactiveException, match="is not active"):
            make_account(status=status).ensure_active()


def test_deposit_increases_balance_and_updates_timestamp() -> None:
    account = make_account()
    old_updated_at = account.updated_at

    account.deposit(Money.of("25.50"))

    assert account.balance == Money.of("125.50")
    assert account.updated_at >= old_updated_at


@pytest.mark.parametrize("amount", ["0", "-1"])
def test_deposit_rejects_zero_or_negative_amount_without_changing_balance(amount: str) -> None:
    account = make_account()
    before = account.balance

    with pytest.raises(InvalidAmountException, match="must be positive"):
        account.deposit(Money.of(amount))

    assert account.balance == before


def test_deposit_rejects_inactive_account() -> None:
    account = make_account(status=AccountStatus.INACTIVE)

    with pytest.raises(AccountInactiveException):
        account.deposit(Money.of("1"))


def test_withdrawal_decreases_balance() -> None:
    account = make_account()
    old_updated_at = account.updated_at

    account.withdraw(Money.of("35.25"))

    assert account.balance == Money.of("64.75")
    assert account.updated_at >= old_updated_at


def test_withdrawal_allows_exact_balance() -> None:
    account = make_account(balance="10")

    account.withdraw(Money.of("10"))

    assert account.balance == Money.zero()


def test_checking_account_can_use_configured_overdraft_limit() -> None:
    account = make_account(
        balance="10",
        account_type=AccountType.CHECKING,
        terms=AccountTerms(overdraft_limit=Decimal(20)),
    )

    account.withdraw(Money.of("30"))

    assert account.balance == Money.of("-20")


def test_checking_account_cannot_exceed_configured_overdraft_limit() -> None:
    account = make_account(
        balance="10",
        account_type=AccountType.CHECKING,
        terms=AccountTerms(overdraft_limit=Decimal(20)),
    )

    with pytest.raises(InsufficientBalanceException):
        account.withdraw(Money.of("30.01"))

    assert account.balance == Money.of("10")


def test_savings_account_cannot_use_overdraft_limit() -> None:
    account = make_account(
        balance="10",
        terms=AccountTerms(overdraft_limit=Decimal(20)),
    )

    with pytest.raises(InsufficientBalanceException):
        account.withdraw(Money.of("11"))
    assert account.balance == Money.of("10")


def test_withdrawal_above_available_balance_is_atomic() -> None:
    account = make_account(balance="10")
    old_updated_at = account.updated_at

    with pytest.raises(InsufficientBalanceException):
        account.withdraw(Money.of("10.01"))

    assert account.balance == Money.of("10")
    assert account.updated_at == old_updated_at


@pytest.mark.parametrize("amount", ["0", "-1"])
def test_withdrawal_rejects_zero_or_negative_amount(amount: str) -> None:
    account = make_account()

    with pytest.raises(InvalidAmountException, match="must be positive"):
        account.withdraw(Money.of(amount))
    assert account.balance == Money.of("100")


def test_withdrawal_rejects_inactive_account() -> None:
    account = make_account(status=AccountStatus.DELETED)

    with pytest.raises(AccountInactiveException):
        account.withdraw(Money.of("1"))


def test_account_state_transitions_update_status_and_timestamps() -> None:
    account = make_account(status=AccountStatus.INACTIVE)
    old_updated_at = account.updated_at

    account.activate()
    assert account.account_status is AccountStatus.ACTIVE
    assert account.updated_at >= old_updated_at

    account.deactivate()
    assert account.account_status is AccountStatus.INACTIVE

    account.mark_deleted()
    assert account.account_status is AccountStatus.DELETED
    assert account.is_deleted
    assert account.deleted_at is not None


def test_account_terms_default_and_explicit_values() -> None:
    account = make_account()
    assert account.terms == AccountTerms()
    assert account.terms is not make_account().terms

    terms = AccountTerms(
        interest_rate=Decimal("0.05"),
        overdraft_limit=Decimal(25),
        term_start_date=date(2026, 1, 1),
        term_end_date=date(2027, 1, 1),
    )
    assert make_account(terms=terms).terms is terms
