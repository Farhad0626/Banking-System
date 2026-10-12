from dataclasses import dataclass
from datetime import datetime


@dataclass
class DepositRequest:
    """Data transfer object for deposit requests."""

    account_id: int
    amount: str


@dataclass
class WithdrawalRequest:
    """Data transfer object for withdrawal requests."""

    account_id: int
    amount: str


@dataclass
class TransferRequest:
    """Data transfer object for transfer requests."""

    from_account_id: int
    to_account_id: int
    amount: str


@dataclass
class TransactionView:
    """Data transfer object for viewing transaction information."""

    transaction_id: int
    transaction_type: str
    amount: str
    source_account_id: int | None
    destination_account_id: int | None
    status: str
    created_at: datetime


@dataclass
class SearchTransactionRequest:
    """Data transfer object for searching transactions."""

    account_id: int | None = None
    transaction_type: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
