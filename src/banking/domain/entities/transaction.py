from dataclasses import dataclass, field
from datetime import UTC, datetime

from banking.domain.enums.transaction_status import TransactionStatus
from banking.domain.enums.transaction_type import TransactionType
from banking.domain.exceptions.transaction_exceptions import (
    InvalidAmountException,
    SameAccountTransferException,
)
from banking.domain.value_objects.money import Money


@dataclass
class Transaction:
    """Entity representing a bank transaction."""

    id: int | None
    transaction_type: TransactionType
    amount: Money
    source_account_id: int | None = None
    destination_account_id: int | None = None
    status: TransactionStatus = TransactionStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not self.amount.is_positive():
            raise InvalidAmountException("Transaction amount must be positive.")

        if self.transaction_type == TransactionType.DEPOSIT and self.source_account_id is not None:
            raise ValueError("Deposit transactions should not have a source account.")

        if (
            self.transaction_type == TransactionType.WITHDRAWAL
            and self.destination_account_id is not None
        ):
            raise ValueError("Withdrawal transactions should not have a destination account.")

        if self.transaction_type == TransactionType.TRANSFER:
            if self.source_account_id is None or self.destination_account_id is None:
                raise ValueError(
                    "Transfer transactions must have both source and destination accounts."
                )
            if self.source_account_id == self.destination_account_id:
                raise SameAccountTransferException(
                    "Source and destination accounts cannot be the same for a transfer."
                )

    def mark_completed(self) -> None:
        """Mark the transaction as completed."""
        self.status = TransactionStatus.COMPLETED

    def mark_failed(self) -> None:
        """Mark the transaction as failed."""
        self.status = TransactionStatus.FAILED
