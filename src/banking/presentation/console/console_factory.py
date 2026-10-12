import getpass
from collections.abc import Callable

from banking.application.context.application_context import ApplicationContext
from banking.presentation.console.account_menu import AccountMenu
from banking.presentation.console.auth_menu import AuthMenu
from banking.presentation.console.customer_menu import CustomerMenu
from banking.presentation.console.error_handler import ErrorHandler
from banking.presentation.console.input_reader import InputReader
from banking.presentation.console.main_menu import MainMenu
from banking.presentation.console.output_writer import OutputWriter
from banking.presentation.console.transaction_menu import TransactionMenu


def build_console(
    app: ApplicationContext,
    *,
    input_fn: Callable[[str], str] = input,
    password_fn: Callable[[str], str] = getpass.getpass,
    print_fn: Callable[..., None] = print,
) -> MainMenu:
    """Create every menu with shared I/O helpers; I/O functions are injectable for tests."""
    writer = OutputWriter(print_fn)
    reader = InputReader(writer, input_fn, password_fn)
    errors = ErrorHandler(writer)

    customer_menu = CustomerMenu(app, reader, writer, errors)
    account_menu = AccountMenu(app, reader, writer, errors)
    transaction_menu = TransactionMenu(app, reader, writer, errors, account_menu)
    auth_menu = AuthMenu(app, reader, writer, errors, customer_menu, account_menu, transaction_menu)
    return MainMenu(app, reader, writer, errors, auth_menu)
