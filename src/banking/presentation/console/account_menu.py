from banking.application.dto.account.account_dto import AccountView, CreateAccountRequest
from banking.presentation.console.base_menu import BaseMenu
from banking.presentation.console.view_formatters import account_table
from banking.shared.constants import ACCOUNT_TYPE_LABELS


class AccountMenu(BaseMenu):
    """Lists and creates accounts, and lets other menus ask the user to pick one of their accounts."""

    def list_accounts(self) -> None:
        """Display all accounts owned by the logged-in customer."""
        session = self._app.require_session()
        accounts = self._app.get_use_case("list_my_accounts").execute(session)
        if not accounts:
            self._writer.info("You have no accounts yet. Use 'Create Account' first.")
            return
        self._writer.title("My Accounts")
        headers, rows = account_table(accounts)
        self._writer.table(headers, rows)

    def create_account(self) -> None:
        """Ask for the account type and initial deposit, then create the account."""
        session = self._app.require_session()
        self._writer.menu("Account type", [label for _, label in ACCOUNT_TYPE_LABELS])
        numbers = [str(number) for number in range(1, len(ACCOUNT_TYPE_LABELS) + 1)]
        choice = self._reader.read_choice("Select account type", numbers)
        account_type = ACCOUNT_TYPE_LABELS[int(choice) - 1][0]
        initial_deposit = self._reader.read_amount("Initial deposit (0 for none)")

        request = CreateAccountRequest(
            customer_id=session.customer_id,
            account_type=account_type,
            initial_deposit=initial_deposit,
        )
        account = self._app.get_use_case("create_account").execute(request, session)
        self._writer.success(f"Account created. Account number: {account.account_number}")

    def choose_account(self, prompt: str) -> AccountView | None:
        """Show the customer's accounts and return the chosen one, or None if none exist or cancelled."""
        session = self._app.require_session()
        accounts = self._app.get_use_case("list_my_accounts").execute(session)
        if not accounts:
            self._writer.info("You have no accounts yet. Use 'Create Account' first.")
            return None
        headers, rows = account_table(accounts)
        self._writer.table(headers, rows)
        valid = ["0"] + [str(number) for number in range(1, len(accounts) + 1)]
        choice = self._reader.read_choice(f"{prompt} (0 to cancel)", valid)
        return None if choice == "0" else accounts[int(choice) - 1]
