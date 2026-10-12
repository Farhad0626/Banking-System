from banking.application.context.session_context import Session
from banking.application.dto.account.account_dto import AccountView
from banking.application.ports.repositories.account_repository import AccountRepository
from banking.domain.exceptions.account_exceptions import AccountNotFoundException
from banking.domain.exceptions.auth_exceptions import AuthenticationFailedException


class GetAccount:
    """Return account details after verifying the account exists and belongs to the current user."""

    def __init__(self, account_repository: AccountRepository) -> None:
        self._accounts = account_repository

    def execute(self, account_id: int, session: Session) -> AccountView:
        account = self._accounts.get_by_id(account_id)
        if account is None or account.is_deleted:
            raise AccountNotFoundException(f"Account with ID {account_id} was not found.")
        if not session.is_owner(account.customer_id.value):
            raise AuthenticationFailedException("Access to this account is not permitted.")

        if account.id is None:
            raise RuntimeError("Account repository returned an account without an ID.")
        return AccountView(
            account_id=account.id,
            account_number=account.account_number.value,
            customer_id=account.customer_id.value,
            account_type=account.account_type.value,
            balance=str(account.balance),
            status=account.account_status.value,
        )
