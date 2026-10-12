from banking.application.context.session_context import Session
from banking.application.dto.account.account_dto import AccountView
from banking.application.ports.repositories.account_repository import AccountRepository


class ListMyAccounts:
    """Returns the accounts of the logged-in customer; the id always comes from the session."""

    def __init__(self, account_repository: AccountRepository) -> None:
        """Store the repository used to read accounts."""
        self._accounts = account_repository

    def execute(self, session: Session) -> list[AccountView]:
        """Return one AccountView per account owned by the session's customer."""
        session.require_active()
        accounts = self._accounts.get_by_customer_id(session.customer_id)

        result = []
        for account in accounts:
            if account.id is None:
                raise RuntimeError("Account repository returned an account without an ID.")
            result.append(
                AccountView(
                    account_id=account.id,
                    account_number=account.account_number.value,
                    customer_id=account.customer_id.value,
                    account_type=account.account_type.value,
                    balance=str(account.balance),
                    status=account.account_status.value,
                )
            )
        return result
