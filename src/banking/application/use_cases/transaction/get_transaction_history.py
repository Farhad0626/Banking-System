from banking.application.context.session_context import Session
from banking.application.dto.transaction.transaction_dto import TransactionView
from banking.application.ports.repositories.account_repository import AccountRepository
from banking.application.ports.repositories.transaction_repository import TransactionRepository
from banking.domain.exceptions.account_exceptions import AccountNotFoundException
from banking.domain.exceptions.auth_exceptions import AuthenticationFailedException


class GetTransactionHistory:
    """Application use case for retrieving an account's transaction history."""

    def __init__(
        self,
        transaction_repository: TransactionRepository,
        account_repository: AccountRepository,
    ) -> None:
        self._transactions = transaction_repository
        self._accounts = account_repository

    def execute(self, account_id: int, session: Session) -> list[TransactionView]:
        account = self._accounts.get_by_id(account_id)
        if account is None:
            raise AccountNotFoundException(f"Account with ID {account_id} was not found.")
        if not session.is_owner(account.customer_id.value):
            raise AuthenticationFailedException(
                "Access to this account's history is not permitted."
            )

        transactions = self._transactions.get_by_account_id(account_id)
        result = []

        for transaction in transactions:
            if transaction.id is None:
                raise RuntimeError("Transaction repository returned a transaction without an ID.")
            result.append(
                TransactionView(
                    transaction_id=transaction.id,
                    transaction_type=transaction.transaction_type.value,
                    amount=str(transaction.amount),
                    source_account_id=transaction.source_account_id,
                    destination_account_id=transaction.destination_account_id,
                    status=transaction.status.value,
                    created_at=transaction.created_at,
                )
            )

        return result
