from banking.application.context.session_context import Session
from banking.application.dto.account.account_dto import AccountLookupView
from banking.application.ports.repositories.account_repository import AccountRepository
from banking.domain.exceptions.account_exceptions import AccountNotFoundException
from banking.domain.value_objects.account_number import AccountNumber


class LookupAccountByNumber:
    """Finds an account by its public number and returns only the data needed to transfer to it."""

    def __init__(self, account_repository: AccountRepository) -> None:
        """Store the repository used to look accounts up."""
        self._accounts = account_repository

    def execute(self, account_number: str, session: Session) -> AccountLookupView:
        """Validate the number's format, then return the matching account's id and number."""
        session.require_active()
        number = AccountNumber(account_number)
        account = self._accounts.get_by_account_number(number.value)
        if account is None or account.is_deleted:
            raise AccountNotFoundException("No account was found with this number.")
        if account.id is None:
            raise RuntimeError("Account repository returned an account without an ID.")
        return AccountLookupView(account_id=account.id, account_number=number.value)
