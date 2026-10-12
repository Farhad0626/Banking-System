from decimal import Decimal, InvalidOperation

from banking.application.context.session_context import Session
from banking.application.dto.transaction.transaction_dto import TransactionView, WithdrawalRequest
from banking.application.ports.persistence.unit_of_work import UnitOfWork
from banking.domain.entities.transaction import Transaction
from banking.domain.enums.transaction_type import TransactionType
from banking.domain.exceptions.account_exceptions import (
    AccountNotFoundException,
    InsufficientBalanceException,
)
from banking.domain.exceptions.auth_exceptions import AuthenticationFailedException
from banking.domain.value_objects.money import Money


class Withdrawl:
    """Application use case for withdrawing money from an account."""

    def __init__(self, unit_of_work: UnitOfWork) -> None:
        self._uow = unit_of_work

    def execute(self, request: WithdrawalRequest, session: Session) -> TransactionView:
        try:
            amount = Money(Decimal(request.amount))
        except InvalidOperation:
            raise ValueError("The withdrawal amount is invalid.")

        with self._uow as uow:
            account = uow.accounts.get_by_id(request.account_id, for_update=True)
            if account is None:
                raise AccountNotFoundException(
                    f"Account with ID {request.account_id} was not found."
                )
            if not session.is_owner(account.customer_id.value):
                raise AuthenticationFailedException("Access to this account is not permitted.")
            if account.id is None:
                raise RuntimeError("Account repository returned an account without an ID.")
            if account.balance < amount:
                raise InsufficientBalanceException("Insufficient funds.")

            account.withdraw(amount)
            uow.accounts.update(account)

            transaction = Transaction(
                id=None,
                transaction_type=TransactionType.WITHDRAWAL,
                amount=amount,
                source_account_id=account.id,
                destination_account_id=None,
            )
            transaction.mark_completed()
            saved = uow.transactions.add(transaction)
            if saved.id is None:
                raise RuntimeError("Transaction repository did not assign an ID.")

            uow.commit()

        return TransactionView(
            transaction_id=saved.id,
            transaction_type=saved.transaction_type.value,
            amount=str(saved.amount),
            source_account_id=saved.source_account_id,
            destination_account_id=saved.destination_account_id,
            status=saved.status.value,
            created_at=saved.created_at,
        )
