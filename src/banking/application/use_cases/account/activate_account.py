from banking.application.ports.repositories.account_repository import AccountRepository
from banking.domain.exceptions.account_exceptions import AccountNotFoundException


class ActivateAccount:
    """Activate an existing account."""

    def __init__(self, account_repository: AccountRepository) -> None:
        self._accounts = account_repository

    def execute(self, account_id: int) -> None:
        account = self._accounts.get_by_id(account_id)
        if account is None:
            raise AccountNotFoundException(f"Account with ID {account_id} was not found.")
        account.activate()
        self._accounts.update(account)
