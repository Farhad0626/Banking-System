from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from banking.application.dto.transaction.transaction_dto import DepositRequest, TransferRequest
from banking.application.use_cases.transaction.deposit import Deposit
from banking.application.use_cases.transaction.get_transaction_history import GetTransactionHistory
from banking.application.use_cases.transaction.transfer_funds import TransferFunds
from banking.domain.enums.account_type import AccountType
from banking.domain.enums.transaction_type import TransactionType
from banking.domain.exceptions.account_exceptions import AccountNotFoundException
from banking.domain.exceptions.auth_exceptions import AuthenticationFailedException
from banking.domain.value_objects.customer_id import CustomerId
from banking.domain.value_objects.money import Money


class UnitOfWorkFake:
    def __init__(self, accounts: dict[int, object], saved_transaction=None):
        self.accounts = Mock()
        self.accounts.get_by_id.side_effect = lambda account_id, for_update=False: accounts.get(
            account_id
        )
        self.transactions = Mock()
        self.transactions.add.side_effect = lambda transaction: saved_transaction or transaction
        self.commit = Mock()
        self.rollback = Mock()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return None


def account(account_id: int, customer_id: int = 7) -> SimpleNamespace:
    return SimpleNamespace(
        id=account_id,
        customer_id=CustomerId(customer_id),
        account_number=SimpleNamespace(value=f"{account_id:016d}"),
        account_type=AccountType.CHECKING,
        balance=Money(Decimal("50.00")),
        ensure_active=Mock(),
        deposit=Mock(),
        withdraw=Mock(),
    )


def test_deposit_missing_account_and_unauthorized_session_do_not_commit() -> None:
    missing_uow = UnitOfWorkFake({})
    session = SimpleNamespace(is_owner=Mock(return_value=True))

    with pytest.raises(AccountNotFoundException):
        Deposit(missing_uow).execute(DepositRequest(4, "10.00"), session)
    missing_uow.commit.assert_not_called()

    target = account(4)
    denied_uow = UnitOfWorkFake({4: target})
    denied = SimpleNamespace(is_owner=Mock(return_value=False))
    with pytest.raises(AuthenticationFailedException):
        Deposit(denied_uow).execute(DepositRequest(4, "10.00"), denied)
    denied_uow.accounts.update.assert_not_called()
    denied_uow.commit.assert_not_called()


def test_deposit_invalid_decimal_is_rejected_before_entering_transaction() -> None:
    uow = UnitOfWorkFake({})

    with pytest.raises(ValueError, match="deposit amount is invalid"):
        Deposit(uow).execute(DepositRequest(4, "invalid"), SimpleNamespace())

    uow.accounts.get_by_id.assert_not_called()
    uow.commit.assert_not_called()


def test_deposit_updates_account_records_completed_transaction_and_commits(monkeypatch) -> None:
    from banking.application.use_cases.transaction import deposit as module

    target = account(4)
    uow = UnitOfWorkFake({4: target})

    def save_transaction(transaction):
        transaction.id = 1
        return transaction

    uow.transactions.add.side_effect = save_transaction
    monkeypatch.setattr(module, "TransactionView", lambda **kwargs: SimpleNamespace(**kwargs))

    view = Deposit(uow).execute(
        DepositRequest(4, "10.25"), SimpleNamespace(is_owner=Mock(return_value=True))
    )

    uow.accounts.get_by_id.assert_called_once_with(4, for_update=True)
    target.deposit.assert_called_once_with(Money(Decimal("10.25")))
    uow.accounts.update.assert_called_once_with(target)
    saved = uow.transactions.add.call_args.args[0]
    assert saved.transaction_type is TransactionType.DEPOSIT
    assert saved.status.value == "COMPLETED"
    assert saved.source_account_id is None
    assert saved.destination_account_id == 4
    uow.commit.assert_called_once_with()
    assert view.amount == "10.25"


def test_transaction_history_checks_account_and_owner_before_loading_history() -> None:
    transactions = Mock()
    accounts = Mock()
    accounts.get_by_id.return_value = None
    use_case = GetTransactionHistory(transactions, accounts)

    with pytest.raises(AccountNotFoundException):
        use_case.execute(4, SimpleNamespace(is_owner=Mock(return_value=True)))
    transactions.get_by_account_id.assert_not_called()

    accounts.get_by_id.return_value = account(4)
    denied = SimpleNamespace(is_owner=Mock(return_value=False))
    with pytest.raises(AuthenticationFailedException):
        use_case.execute(4, denied)
    transactions.get_by_account_id.assert_not_called()


def test_transaction_history_maps_transactions_for_owner() -> None:
    accounts = Mock()
    accounts.get_by_id.return_value = account(4)
    transactions = Mock()
    transactions.get_by_account_id.return_value = [
        SimpleNamespace(
            id=3,
            transaction_type=TransactionType.DEPOSIT,
            amount=Money(Decimal("5.00")),
            source_account_id=None,
            destination_account_id=4,
            status=SimpleNamespace(value="COMPLETED"),
            created_at=SimpleNamespace(),
        )
    ]

    result = GetTransactionHistory(transactions, accounts).execute(
        4, SimpleNamespace(is_owner=Mock(return_value=True))
    )

    transactions.get_by_account_id.assert_called_once_with(4)
    assert len(result) == 1
    assert result[0].transaction_id == 3
    assert result[0].transaction_type == "DEPOSIT"
    assert result[0].amount == "5.00"
    assert result[0].destination_account_id == 4
    assert result[0].status == "COMPLETED"


def test_transfer_locks_accounts_in_order_updates_both_and_commits(monkeypatch) -> None:
    from banking.application.use_cases.transaction import transfer_funds as module

    request = TransferRequest(from_account_id=10, to_account_id=2, amount="5.00")
    source, destination = account(10), account(2)
    uow = UnitOfWorkFake({2: destination, 10: source})
    transfer_service = Mock()
    monkeypatch.setattr(module, "TransactionView", lambda **kwargs: SimpleNamespace(**kwargs))

    def save_transaction(transaction):
        transaction.id = 1
        return transaction

    uow.transactions.add.side_effect = save_transaction

    result = TransferFunds(uow, transfer_service).execute(
        request, SimpleNamespace(is_owner=Mock(return_value=True))
    )

    assert [call.args[0] for call in uow.accounts.get_by_id.call_args_list] == [2, 10]
    transfer_service.transfer.assert_called_once_with(source, destination, Money(Decimal("5.00")))
    uow.accounts.update.assert_any_call(source)
    uow.accounts.update.assert_any_call(destination)
    uow.commit.assert_called_once_with()
    assert result.source_account_id == 10
    assert result.destination_account_id == 2


def test_transfer_rejects_bad_amount_before_opening_uow() -> None:
    uow = UnitOfWorkFake({})
    with pytest.raises(ValueError, match="transfer amount"):
        TransferFunds(uow, Mock()).execute(
            SimpleNamespace(source_account_id=1, destination_account_id=2, amount="bad"),
            SimpleNamespace(),
        )
    uow.accounts.get_by_id.assert_not_called()


def test_search_and_transfer_dto_field_names_are_covered() -> None:
    request = TransferRequest(1, 2, "3.00")
    assert request.from_account_id == 1
    assert request.to_account_id == 2
    assert not hasattr(request, "source_account_id")
