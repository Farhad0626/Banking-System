from datetime import UTC, datetime
from types import SimpleNamespace

from banking.application.context.application_context import ApplicationContext
from banking.application.context.session_context import Session
from banking.application.dto.account.account_dto import AccountView
from banking.application.dto.customer.customer_dto import CustomerView
from banking.presentation.console.account_menu import AccountMenu
from banking.presentation.console.customer_menu import CustomerMenu
from banking.presentation.console.error_handler import ErrorHandler
from banking.presentation.console.input_reader import InputReader
from banking.presentation.console.main_menu import MainMenu
from banking.presentation.console.output_writer import OutputWriter


def test_account_menu_selects_account_and_supports_cancel_and_empty_list() -> None:
    account = AccountView(10, 3, "0000000000000010", "SAVINGS", "20.00", "ACTIVE")
    session = Session(3, "CUSTOMER", datetime.now(UTC))
    accounts = [account]

    class ListAccounts:
        def execute(self, requested_session):
            assert requested_session is session
            return accounts

    app = ApplicationContext(
        {"list_my_accounts": ListAccounts()},
        current_session=session,
    )
    inputs = iter(["1", "0"])
    output: list[str] = []
    writer = OutputWriter(output.append)
    menu = AccountMenu(
        app,
        InputReader(writer, input_fn=lambda _: next(inputs)),
        writer,
        ErrorHandler(writer),
    )

    assert menu.choose_account("Choose") == account
    assert menu.choose_account("Choose") is None

    accounts.clear()
    assert menu.choose_account("Choose") is None
    assert "[INFO] You have no accounts yet. Use 'Create Account' first." in output


def test_main_menu_exits_cleanly_on_eof_and_invalidates_session() -> None:
    session = Session(3, "CUSTOMER", datetime.now(UTC))
    app = ApplicationContext({}, current_session=session)
    output: list[str] = []
    writer = OutputWriter(lambda *values: output.append(" ".join(map(str, values))))
    menu = MainMenu(
        app,
        InputReader(writer, input_fn=lambda _: _raise_eof()),
        writer,
        ErrorHandler(writer),
        auth_menu=SimpleNamespace(
            register=lambda: None,
            login=lambda: False,
            run=lambda: None,
        ),
    )

    menu.run()

    assert session.is_active is False
    assert app.current_session is None
    assert output[-1] == "[INFO] Goodbye!"


def test_customer_menu_shows_profile_fields() -> None:
    session = Session(3, "CUSTOMER", datetime.now(UTC))

    class GetCustomer:
        def execute(self, customer_id: int, requested_session: Session) -> CustomerView:
            assert customer_id == 3
            assert requested_session is session
            return CustomerView(
                3, "Ada", "Lovelace", "123", "555", "ada@example.test", "ada", True, False
            )

    app = ApplicationContext(
        {"get_customer": GetCustomer()},
        current_session=session,
    )
    output: list[str] = []
    writer = OutputWriter(lambda *values: output.append(" ".join(map(str, values))))
    menu = CustomerMenu(
        app,
        InputReader(writer),
        writer,
        ErrorHandler(writer),
    )

    menu.show_profile()

    assert any("Name" in line and line.endswith("Ada Lovelace") for line in output)
    assert any("Username" in line and line.endswith("ada") for line in output)
    assert all("password" not in line.lower() for line in output)


def _raise_eof() -> str:
    raise EOFError
