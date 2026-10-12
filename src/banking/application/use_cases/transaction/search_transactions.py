from banking.application.context.session_context import Session
from banking.application.dto.transaction.transaction_dto import (
    SearchTransactionRequest,
    TransactionView,
)
from banking.application.ports.repositories.account_repository import AccountRepository
from banking.application.ports.repositories.transaction_repository import TransactionRepository
from banking.domain.exceptions.account_exceptions import AccountNotFoundException
from banking.domain.exceptions.auth_exceptions import AuthenticationFailedException


class SearchTransactions:
    """Application use case for searching transactions based on specified criteria."""

    def __init__(
        self,
        transaction_repository: TransactionRepository,
        account_repository: AccountRepository,
    ) -> None:
        self._transactions = transaction_repository
        self._accounts = account_repository

    def execute(self, request: SearchTransactionRequest, session: Session) -> list[TransactionView]:
        if request.account_id is None:
            raise ValueError("To perform a search, the account ID must be specified.")
        account = self._accounts.get_by_id(request.account_id)
        if account is None or account.is_deleted:
            raise AccountNotFoundException(f"Account with ID {request.account_id} was not found.")
        if not session.is_owner(account.customer_id.value):
            raise AuthenticationFailedException("Access to this account is not permitted.")

        transactions = self._transactions.search(
            account_id=request.account_id,
            transaction_type=request.transaction_type,
            start_date=request.start_date,
            end_date=request.end_date,
        )

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
