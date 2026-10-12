from decimal import Decimal, InvalidOperation

from banking.application.context.session_context import Session
from banking.application.dto.transaction.transaction_dto import TransactionView, TransferRequest
from banking.application.ports.persistence.unit_of_work import UnitOfWork
from banking.domain.entities.transaction import Transaction
from banking.domain.enums.transaction_type import TransactionType
from banking.domain.exceptions.account_exceptions import AccountNotFoundException
from banking.domain.exceptions.auth_exceptions import AuthenticationFailedException
from banking.domain.services.transfer_service import TransferService
from banking.domain.value_objects.money import Money


class TransferFunds:
    """Application use case for transferring money between two accounts."""

    def __init__(self, unit_of_work: UnitOfWork, transfer_service: TransferService) -> None:
        self._uow = unit_of_work
        self._transfer_service = transfer_service

    def execute(self, request: TransferRequest, session: Session) -> TransactionView:
        try:
            amount = Money(Decimal(request.amount))
        except InvalidOperation:
            raise ValueError("Invalid transfer amount.")

        with self._uow as uow:
            locked = {
                account_id: uow.accounts.get_by_id(account_id, for_update=True)
                for account_id in sorted({request.from_account_id, request.to_account_id})
            }
            source = locked[request.from_account_id]
            destination = locked[request.to_account_id]

            if source is None:
                raise AccountNotFoundException(
                    f"Source account with ID {request.from_account_id} not found."
                )
            if destination is None:
                raise AccountNotFoundException(
                    f"Destination account with ID {request.to_account_id} not found."
                )
            if not session.is_owner(source.customer_id.value):
                raise AuthenticationFailedException(
                    "Access to the source account is not permitted."
                )
            if source.id is None or destination.id is None:
                raise RuntimeError("Account repository returned an account without an ID.")

            self._transfer_service.transfer(source, destination, amount)

            uow.accounts.update(source)
            uow.accounts.update(destination)

            transaction = Transaction(
                id=None,
                transaction_type=TransactionType.TRANSFER,
                amount=amount,
                source_account_id=source.id,
                destination_account_id=destination.id,
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
