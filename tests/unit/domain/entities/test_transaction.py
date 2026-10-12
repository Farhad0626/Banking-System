import pytest

from banking.domain.entities.transaction import Transaction
from banking.domain.enums.transaction_status import TransactionStatus
from banking.domain.enums.transaction_type import TransactionType
from banking.domain.exceptions.transaction_exceptions import (
    InvalidAmountException,
    SameAccountTransferException,
)
from banking.domain.value_objects.money import Money


def make_transaction(
    transaction_type: TransactionType,
    *,
    amount: str = "10",
    source: int | None = None,
    destination: int | None = None,
) -> Transaction:
    return Transaction(
        id=1,
        transaction_type=transaction_type,
        amount=Money.of(amount),
        source_account_id=source,
        destination_account_id=destination,
    )


def test_deposit_requires_positive_amount_and_no_source_account() -> None:
    transaction = make_transaction(TransactionType.DEPOSIT, destination=2)
    assert transaction.status is TransactionStatus.PENDING

    with pytest.raises(ValueError, match="should not have a source"):
        make_transaction(TransactionType.DEPOSIT, source=1)


def test_withdrawal_requires_positive_amount_and_no_destination_account() -> None:
    make_transaction(TransactionType.WITHDRAWAL, source=1)

    with pytest.raises(ValueError, match="should not have a destination"):
        make_transaction(TransactionType.WITHDRAWAL, destination=2)


@pytest.mark.parametrize("transaction_type", list(TransactionType))
@pytest.mark.parametrize("amount", ["0", "-0.01"])
def test_all_transaction_types_reject_non_positive_amounts(
    transaction_type: TransactionType, amount: str
) -> None:
    with pytest.raises(InvalidAmountException, match="must be positive"):
        make_transaction(transaction_type, amount=amount)


@pytest.mark.parametrize(
    ("source", "destination"),
    [(None, 2), (1, None), (None, None)],
)
def test_transfer_requires_both_accounts(source: int | None, destination: int | None) -> None:
    with pytest.raises(ValueError, match="must have both"):
        make_transaction(TransactionType.TRANSFER, source=source, destination=destination)


def test_transfer_rejects_same_source_and_destination() -> None:
    with pytest.raises(SameAccountTransferException, match="cannot be the same"):
        make_transaction(TransactionType.TRANSFER, source=1, destination=1)


def test_transfer_accepts_distinct_accounts() -> None:
    transaction = make_transaction(TransactionType.TRANSFER, source=1, destination=2)

    assert transaction.source_account_id == 1
    assert transaction.destination_account_id == 2
    assert transaction.status is TransactionStatus.PENDING


def test_transaction_status_transitions() -> None:
    transaction = make_transaction(TransactionType.DEPOSIT)

    transaction.mark_completed()
    assert transaction.status is TransactionStatus.COMPLETED

    transaction.mark_failed()
    assert transaction.status is TransactionStatus.FAILED
