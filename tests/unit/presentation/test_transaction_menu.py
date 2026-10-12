from datetime import UTC, datetime
from types import SimpleNamespace

from banking.application.context.application_context import ApplicationContext
from banking.application.context.session_context import Session
from banking.application.dto.account.account_dto import AccountLookupView, AccountView
from banking.application.dto.transaction.transaction_dto import (
    SearchTransactionRequest,
    TransferRequest,
    WithdrawalRequest,
)
from banking.presentation.console.error_handler import ErrorHandler
from banking.presentation.console.input_reader import InputReader
from banking.presentation.console.output_writer import OutputWriter
from banking.presentation.console.transaction_menu import TransactionMenu


class RecordingUseCase:
    def __init__(self, result) -> None:
        self.result = result
        self.calls: list[tuple[object, ...]] = []

    def execute(self, *args):
        self.calls.append(args)
        return self.result


class AccountMenuStub:
    def __init__(self, account: AccountView | None) -> None:
        self.account = account

    def choose_account(self, prompt: str) -> AccountView | None:
        assert prompt
        return self.account


def make_menu(
    use_cases: dict[str, object],
    account: AccountView | None,
    user_inputs: list[str] | None = None,
) -> tuple[TransactionMenu, list[str]]:
    session = Session(7, "CUSTOMER", datetime.now(UTC))
    app = ApplicationContext(use_cases, current_session=session)
    output: list[str] = []
    writer = OutputWriter(lambda *values: output.append(" ".join(map(str, values))))
    values = iter(user_inputs or [])
    menu = TransactionMenu(
        app,
        InputReader(writer, input_fn=lambda _: next(values)),
        writer,
        ErrorHandler(writer),
        AccountMenuStub(account),
    )
    return menu, output


def test_withdraw_builds_request_and_reports_transaction_and_balance() -> None:
    account = AccountView(18, 7, "00018", "SAVINGS", "25.00", "ACTIVE")
    withdrawal = RecordingUseCase(SimpleNamespace(transaction_id=90))
    balance = RecordingUseCase("12.50")
    menu, output = make_menu(
        {"withdraw": withdrawal, "get_balance": balance},
        account,
        ["12.50"],
    )

    menu.withdraw()

    request, session = withdrawal.calls[0]
    assert request == WithdrawalRequest(18, "12.50")
    assert session.customer_id == 7
    assert balance.calls[0][0] == 18
    assert "[OK] Withdrawal completed (transaction #90)." in output
    assert "[INFO] New balance: 12.50" in output


def test_transfer_normalizes_destination_number_and_executes_after_confirmation() -> None:
    source = AccountView(18, 7, "00018", "SAVINGS", "25.00", "ACTIVE")
    destination = AccountLookupView(29, "00029")
    lookup = RecordingUseCase(destination)
    transfer = RecordingUseCase(SimpleNamespace(transaction_id=91))
    balance = RecordingUseCase("10.00")
    menu, output = make_menu(
        {
            "lookup_account_by_number": lookup,
            "transfer_funds": transfer,
            "get_balance": balance,
        },
        source,
        ["۰۰۰۲۹", "15.00", "y"],
    )

    menu.transfer()

    assert lookup.calls[0][0] == "00029"
    request, session = transfer.calls[0]
    assert request == TransferRequest(18, 29, "15.00")
    assert session.customer_id == 7
    assert balance.calls[0][0] == 18
    assert "[OK] Transfer completed (transaction #91)." in output


def test_transfer_cancel_does_not_execute_transfer() -> None:
    source = AccountView(18, 7, "00018", "SAVINGS", "25.00", "ACTIVE")
    destination = AccountLookupView(29, "00029")
    transfer = RecordingUseCase(SimpleNamespace(transaction_id=91))
    menu, output = make_menu(
        {
            "lookup_account_by_number": RecordingUseCase(destination),
            "transfer_funds": transfer,
            "get_balance": RecordingUseCase("10.00"),
        },
        source,
        ["00029", "15.00", "n"],
    )

    menu.transfer()

    assert transfer.calls == []
    assert "[INFO] Transfer cancelled." in output


def test_history_displays_no_transactions_message() -> None:
    account = AccountView(18, 7, "00018", "SAVINGS", "25.00", "ACTIVE")
    history = RecordingUseCase([])
    menu, output = make_menu({"get_transaction_history": history}, account)

    menu.history()

    assert history.calls[0][0] == 18
    assert history.calls[0][1].customer_id == 7
    assert "[INFO] No transactions found." in output


def test_search_passes_account_type_and_utc_date_range_to_use_case() -> None:
    account = AccountView(18, 7, "00018", "SAVINGS", "25.00", "ACTIVE")
    search = RecordingUseCase([])
    menu, output = make_menu(
        {"search_transactions": search},
        account,
        ["withdrawal", "2026-01-01", "2026-01-02"],
    )

    menu.search()

    request, session = search.calls[0]
    assert request == SearchTransactionRequest(
        account_id=18,
        transaction_type="WITHDRAWAL",
        start_date=datetime(2026, 1, 1, tzinfo=UTC),
        end_date=datetime(2026, 1, 2, 23, 59, 59, 999999, tzinfo=UTC),
    )
    assert session.customer_id == 7
    assert "[INFO] No transactions found." in output
