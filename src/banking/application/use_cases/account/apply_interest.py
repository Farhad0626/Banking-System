from banking.application.ports.repositories.account_repository import AccountRepository
from banking.domain.exceptions.account_exceptions import AccountNotFoundException
from banking.domain.services.interest_calculator import InterestCalculator


class ApplyInterest:
    """Calculate the account interest and apply it when the calculated interest is positive."""

    def __init__(
        self,
        account_repository: AccountRepository,
        interest_calculator: InterestCalculator,
    ) -> None:
        self._accounts = account_repository
        self._calculator = interest_calculator

    def execute(self, account_id: int) -> str:
        account = self._accounts.get_by_id(account_id)
        if account is None:
            raise AccountNotFoundException(f"Account with ID {account_id} was not found.")

        interest = self._calculator.calculate_interest(account)
        if interest.is_positive():
            account.deposit(interest)
            self._accounts.update(account)

        return str(interest)
