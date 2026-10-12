from banking.application.context.application_context import ApplicationContext
from banking.application.dto.transaction.transaction_dto import (
    DepositRequest,
    SearchTransactionRequest,
    TransactionView,
    TransferRequest,
    WithdrawalRequest,
)
from banking.presentation.console.account_menu import AccountMenu
from banking.presentation.console.base_menu import BaseMenu
from banking.presentation.console.error_handler import ErrorHandler
from banking.presentation.console.input_reader import InputReader
from banking.presentation.console.output_writer import OutputWriter
from banking.presentation.console.view_formatters import transaction_table
from banking.shared.constants import HISTORY_DISPLAY_LIMIT, TRANSACTION_TYPES


class TransactionMenu(BaseMenu):
    """Deposit, withdraw, transfer, history and search screens."""

    def __init__(
        self,
        app: ApplicationContext,
        reader: InputReader,
        writer: OutputWriter,
        errors: ErrorHandler,
        account_menu: AccountMenu,
    ) -> None:
        """Keep the account menu used to let the user pick one of their accounts."""
        super().__init__(app, reader, writer, errors)
        self._account_menu = account_menu

    def deposit(self) -> None:
        """Deposit money into one of the customer's accounts."""
        session = self._app.require_session()
        account = self._account_menu.choose_account("Deposit to which account?")
        if account is None:
            return
        amount = self._reader.read_amount("Amount")
        result = self._app.get_use_case("deposit").execute(
            DepositRequest(account_id=account.account_id, amount=amount), session
        )
        balance = self._app.get_use_case("get_balance").execute(account.account_id, session)
        self._writer.success(f"Deposit completed (transaction #{result.transaction_id}).")
        self._writer.info(f"New balance: {balance}")

    def withdraw(self) -> None:
        """Withdraw money from one of the customer's accounts."""
        session = self._app.require_session()
        account = self._account_menu.choose_account("Withdraw from which account?")
        if account is None:
            return
        amount = self._reader.read_amount("Amount")
        result = self._app.get_use_case("withdraw").execute(
            WithdrawalRequest(account_id=account.account_id, amount=amount), session
        )
        balance = self._app.get_use_case("get_balance").execute(account.account_id, session)
        self._writer.success(f"Withdrawal completed (transaction #{result.transaction_id}).")
        self._writer.info(f"New balance: {balance}")

    def transfer(self) -> None:
        """Transfer money from one of the customer's accounts to any account number."""
        session = self._app.require_session()
        source = self._account_menu.choose_account("Transfer from which account?")
        if source is None:
            return
        number = self._reader.read_text("Destination account number", normalize_digits=True)
        destination = self._app.get_use_case("lookup_account_by_number").execute(number, session)
        amount = self._reader.read_amount("Amount")

        self._writer.key_values(
            [
                ("From", source.account_number),
                ("To", destination.account_number),
                ("Amount", amount),
            ]
        )
        if not self._reader.confirm("Confirm transfer?"):
            self._writer.info("Transfer cancelled.")
            return

        result = self._app.get_use_case("transfer_funds").execute(
            TransferRequest(
                from_account_id=source.account_id,
                to_account_id=destination.account_id,
                amount=amount,
            ),
            session,
        )
        balance = self._app.get_use_case("get_balance").execute(source.account_id, session)
        self._writer.success(f"Transfer completed (transaction #{result.transaction_id}).")
        self._writer.info(f"New balance of {source.account_number}: {balance}")

    def history(self) -> None:
        """Show the transaction history of one of the customer's accounts."""
        session = self._app.require_session()
        account = self._account_menu.choose_account("Show history of which account?")
        if account is None:
            return
        transactions = self._app.get_use_case("get_transaction_history").execute(
            account.account_id, session
        )
        self._show_transactions(transactions, account.account_id)

    def search(self) -> None:
        """Search one account's transactions by type and date range."""
        session = self._app.require_session()
        account = self._account_menu.choose_account("Search which account?")
        if account is None:
            return
        transaction_type = self._reader.read_optional_choice(
            "Type (DEPOSIT/WITHDRAWAL/TRANSFER, Enter for all)", TRANSACTION_TYPES
        )
        date_from = self._reader.read_optional_date("From date YYYY-MM-DD (Enter to skip)")
        date_to = self._reader.read_optional_date(
            "To date YYYY-MM-DD (Enter to skip)", end_of_day=True
        )
        transactions = self._app.get_use_case("search_transactions").execute(
            SearchTransactionRequest(
                account_id=account.account_id,
                transaction_type=transaction_type,
                start_date=date_from,
                end_date=date_to,
            ),
            session,
        )
        self._show_transactions(transactions, account.account_id)

    def _show_transactions(self, transactions: list[TransactionView], account_id: int) -> None:
        """Print up to HISTORY_DISPLAY_LIMIT transactions (newest first) or an empty-state message."""
        if not transactions:
            self._writer.info("No transactions found.")
            return
        shown = transactions[:HISTORY_DISPLAY_LIMIT]
        headers, rows = transaction_table(shown, account_id)
        self._writer.table(headers, rows)
        if len(transactions) > len(shown):
            self._writer.info(
                f"Showing the latest {len(shown)} of {len(transactions)} transactions."
            )
