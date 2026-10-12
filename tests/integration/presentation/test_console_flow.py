from datetime import UTC, datetime

from banking.application.context.application_context import ApplicationContext
from banking.application.context.session_context import Session
from banking.application.dto.account.account_dto import AccountView
from banking.application.dto.auth.login_dto import LoginResult
from banking.application.dto.transaction.transaction_dto import (
    DepositRequest,
    TransactionView,
)
from banking.application.use_cases.auth.logout import Logout
from banking.presentation.console.console_factory import build_console


class LoginStub:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.request = None

    def execute(self, request):
        self.request = request
        return LoginResult(self.session.customer_id, self.session.role), self.session


class AccountListStub:
    def __init__(self, account: AccountView) -> None:
        self.account = account

    def execute(self, session: Session) -> list[AccountView]:
        assert session.customer_id == self.account.customer_id
        return [self.account]


class DepositStub:
    def __init__(self) -> None:
        self.request: DepositRequest | None = None
        self.session: Session | None = None

    def execute(self, request: DepositRequest, session: Session) -> TransactionView:
        self.request = request
        self.session = session
        return TransactionView(
            transaction_id=52,
            transaction_type="DEPOSIT",
            amount=request.amount,
            source_account_id=None,
            destination_account_id=request.account_id,
            status="COMPLETED",
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )


class BalanceStub:
    def execute(self, account_id: int, session: Session) -> str:
        assert account_id == 18
        assert session.customer_id == 7
        return "35.00"


def test_console_login_deposit_and_logout_flow() -> None:
    session = Session(7, "CUSTOMER", datetime.now(UTC))
    account = AccountView(18, 7, "0000000000000018", "SAVINGS", "25.00", "ACTIVE")
    login = LoginStub(session)
    deposit = DepositStub()
    use_cases = {
        "login": login,
        "list_my_accounts": AccountListStub(account),
        "deposit": deposit,
        "get_balance": BalanceStub(),
        "logout": Logout(),
    }
    app = ApplicationContext(use_cases)
    user_inputs = iter(["2", "ada", "4", "1", "10.00", "10", "3"])
    passwords = iter(["correct horse"])
    output: list[str] = []

    def capture(*values: object) -> None:
        output.append(" ".join(map(str, values)))

    console = build_console(
        app,
        input_fn=lambda _: next(user_inputs),
        password_fn=lambda _: next(passwords),
        print_fn=capture,
    )

    console.run()

    assert login.request is not None
    assert login.request.username == "ada"
    assert login.request.password == "correct horse"
    assert deposit.request == DepositRequest(account_id=18, amount="10.00")
    assert deposit.session is session
    assert session.is_active is False
    assert app.current_session is None
    assert "[OK] Deposit completed (transaction #52)." in output
    assert "[INFO] New balance: 35.00" in output
    assert "[OK] You have been logged out." in output
    assert output[-1] == "[INFO] Goodbye!"
