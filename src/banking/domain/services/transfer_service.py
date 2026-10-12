from banking.domain.entities.account import Account
from banking.domain.exceptions.transaction_exceptions import SameAccountTransferException
from banking.domain.value_objects.money import Money


class TransferService:
    """Service for handling money transfers between accounts."""

    @staticmethod
    def transfer(source_account: Account, destination_account: Account, amount: Money) -> None:
        """Transfer money from one account to another."""
        if source_account.account_number == destination_account.account_number:
            raise SameAccountTransferException("Cannot transfer to the same account.")

        source_account.ensure_active()
        destination_account.ensure_active()

        source_account.withdraw(amount)
        destination_account.deposit(amount)
