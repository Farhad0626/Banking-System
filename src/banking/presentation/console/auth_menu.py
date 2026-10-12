from banking.application.context.application_context import ApplicationContext
from banking.application.dto.auth.change_password_dto import ChangePasswordRequest
from banking.application.dto.auth.login_dto import LoginRequest
from banking.application.dto.auth.register_dto import RegisterCustomerRequest
from banking.domain.exceptions.domain_exception import DomainException
from banking.presentation.console.account_menu import AccountMenu
from banking.presentation.console.base_menu import BaseMenu, MenuOption
from banking.presentation.console.customer_menu import CustomerMenu
from banking.presentation.console.error_handler import ErrorHandler
from banking.presentation.console.input_reader import InputReader
from banking.presentation.console.output_writer import OutputWriter
from banking.presentation.console.transaction_menu import TransactionMenu


class AuthMenu(BaseMenu):
    """Owns the authentication flows and the menu shown to a logged-in customer."""

    def __init__(
        self,
        app: ApplicationContext,
        reader: InputReader,
        writer: OutputWriter,
        errors: ErrorHandler,
        customer_menu: CustomerMenu,
        account_menu: AccountMenu,
        transaction_menu: TransactionMenu,
    ) -> None:
        """Keep the sub-menus this menu delegates to."""
        super().__init__(app, reader, writer, errors)
        self._customers = customer_menu
        self._accounts = account_menu
        self._transactions = transaction_menu

    def register(self) -> None:
        """Collect registration details and create the customer, allowing corrections on failure."""
        self._writer.title("Register")
        details: dict[str, str] = {}
        while True:
            details = self._ask_registration_details(details)
            password = self._ask_new_password("Password")
            request = RegisterCustomerRequest(**details, password=password)
            try:
                result = self._app.get_use_case("register_customer").execute(request)
            except (DomainException, ValueError) as error:
                self._errors.report(error)
                if not self._reader.confirm("Edit your details and try again?"):
                    return
                continue
            self._writer.success(f"Registration successful. You can now log in, {result.username}.")
            return

    def login(self) -> bool:
        """Ask for credentials and start a session; returns True when login succeeded."""
        self._writer.title("Login")
        username = self._reader.read_text("Username")
        password = self._reader.read_password("Password")
        _, session = self._app.get_use_case("login").execute(
            LoginRequest(username=username, password=password)
        )
        self._app.start_session(session)
        self._writer.success(f"Welcome, {username}!")
        return True

    def run(self) -> None:
        """Show the logged-in menu until the customer logs out."""
        options = [
            MenuOption("Customer Profile", self._customers.show_profile),
            MenuOption("My Accounts", self._accounts.list_accounts),
            MenuOption("Create Account", self._accounts.create_account),
            MenuOption("Deposit", self._transactions.deposit),
            MenuOption("Withdraw", self._transactions.withdraw),
            MenuOption("Transfer", self._transactions.transfer),
            MenuOption("Transaction History", self._transactions.history),
            MenuOption("Search Transactions", self._transactions.search),
            MenuOption("Change Password", self.change_password),
            MenuOption("Logout", self.logout),
        ]
        self._run_loop("Customer Menu", options, keep_running=lambda: self._app.is_authenticated)

    def change_password(self) -> None:
        """Change the logged-in customer's password after verifying the current one."""
        session = self._app.require_session()
        old_password = self._reader.read_password("Current password")
        new_password = self._ask_new_password("New password")
        self._app.get_use_case("change_password").execute(
            ChangePasswordRequest(
                customer_id=session.customer_id,
                old_password=old_password,
                new_password=new_password,
            ),
            session,
        )
        self._writer.success("Password changed successfully.")

    def logout(self) -> bool:
        """End the session and leave the logged-in menu."""
        self._app.get_use_case("logout").execute(self._app.current_session)
        self._app.end_session()
        self._writer.success("You have been logged out.")
        return True

    def _ask_registration_details(self, previous: dict[str, str]) -> dict[str, str]:
        """Prompt for every registration field, offering earlier answers as defaults."""
        ask = self._reader.read_text
        return {
            "first_name": ask("First name", default=previous.get("first_name")),
            "last_name": ask("Last name", default=previous.get("last_name")),
            "national_id": ask(
                "National ID", default=previous.get("national_id"), normalize_digits=True
            ),
            "mobile": ask(
                "Mobile (09xxxxxxxxx)", default=previous.get("mobile"), normalize_digits=True
            ),
            "email": ask("Email", default=previous.get("email")),
            "username": ask("Username", default=previous.get("username")),
        }

    def _ask_new_password(self, label: str) -> str:
        """Ask for a password twice until both entries match."""
        while True:
            first = self._reader.read_password(label)
            second = self._reader.read_password(f"Confirm {label.lower()}")
            if first == second:
                return first
            self._writer.error("Passwords do not match. Please try again.")
