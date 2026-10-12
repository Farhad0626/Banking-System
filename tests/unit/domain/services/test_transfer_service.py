import pytest

from banking.domain.entities.account import Account
from banking.domain.enums.account_status import AccountStatus
from banking.domain.enums.account_type import AccountType
from banking.domain.exceptions.account_exceptions import AccountInactiveException
from banking.domain.exceptions.insufficient_balance import InsufficientBalanceException
from banking.domain.exceptions.transaction_exceptions import (
    InvalidAmountException,
    SameAccountTransferException,
)
from banking.domain.services.transfer_service import TransferService
from banking.domain.value_objects.account_number import AccountNumber
from banking.domain.value_objects.customer_id import CustomerId
from banking.domain.value_objects.money import Money


def make_account(
    account_number: str,
    balance: str,
    status: AccountStatus = AccountStatus.ACTIVE,
) -> Account:
    return Account(
        id=1,
        account_number=AccountNumber(account_number),
        customer_id=CustomerId(1),
        account_type=AccountType.SAVINGS,
        account_status=status,
        balance=Money.of(balance),
    )


def test_transfer_debits_source_and_credits_destination() -> None:
    source = make_account("1111111111111111", "100")
    destination = make_account("2222222222222222", "20")

    result = TransferService.transfer(source, destination, Money.of("35.50"))

    assert result is None
    assert source.balance == Money.of("64.50")
    assert destination.balance == Money.of("55.50")


def test_transfer_rejects_same_account_without_mutation() -> None:
    account = make_account("1111111111111111", "100")

    with pytest.raises(SameAccountTransferException, match="same account"):
        TransferService.transfer(account, account, Money.of("1"))
    assert account.balance == Money.of("100")


def test_transfer_rejects_different_objects_with_same_account_number() -> None:
    source = make_account("1111111111111111", "100")
    destination = make_account("1111111111111111", "20")

    with pytest.raises(SameAccountTransferException):
        TransferService.transfer(source, destination, Money.of("1"))
    assert source.balance == Money.of("100")
    assert destination.balance == Money.of("20")


def test_transfer_checks_both_accounts_before_debiting_source() -> None:
    source = make_account("1111111111111111", "100")
    destination = make_account("2222222222222222", "20", AccountStatus.INACTIVE)

    with pytest.raises(AccountInactiveException):
        TransferService.transfer(source, destination, Money.of("10"))
    assert source.balance == Money.of("100")
    assert destination.balance == Money.of("20")


def test_transfer_insufficient_funds_leaves_both_balances_unchanged() -> None:
    source = make_account("1111111111111111", "10")
    destination = make_account("2222222222222222", "20")

    with pytest.raises(InsufficientBalanceException):
        TransferService.transfer(source, destination, Money.of("11"))
    assert source.balance == Money.of("10")
    assert destination.balance == Money.of("20")


@pytest.mark.parametrize("amount", ["0", "-1"])
def test_transfer_rejects_non_positive_amount_without_mutation(amount: str) -> None:
    source = make_account("1111111111111111", "10")
    destination = make_account("2222222222222222", "20")

    with pytest.raises(InvalidAmountException):
        TransferService.transfer(source, destination, Money.of(amount))
    assert source.balance == Money.of("10")
    assert destination.balance == Money.of("20")
