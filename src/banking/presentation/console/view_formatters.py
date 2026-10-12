from collections.abc import Sequence
from datetime import UTC

from banking.application.dto.account.account_dto import AccountView
from banking.application.dto.customer.customer_dto import CustomerView
from banking.application.dto.transaction.transaction_dto import TransactionView


def account_table(accounts: Sequence[AccountView]) -> tuple[list[str], list[list[object]]]:
    """Return headers and numbered rows describing the given accounts."""
    headers = ["#", "Account Number", "Type", "Balance", "Status"]
    rows = [
        [index, a.account_number, a.account_type, a.balance, a.status]
        for index, a in enumerate(accounts, start=1)
    ]
    return headers, rows


def customer_lines(customer: CustomerView) -> list[tuple[str, str]]:
    """Return label/value pairs describing a customer's profile (never includes secrets)."""
    status = "Active" if customer.is_active else "Inactive"
    if customer.is_restricted:
        status += " (restricted)"
    return [
        ("Customer ID", str(customer.customer_id)),
        ("Name", f"{customer.first_name} {customer.last_name}"),
        ("National ID", customer.national_id),
        ("Mobile", customer.mobile),
        ("Email", customer.email),
        ("Username", customer.username),
        ("Status", status),
    ]


def _direction(transaction: TransactionView, account_id: int) -> str:
    """Return IN/OUT from the point of view of the given account."""
    if transaction.transaction_type == "DEPOSIT":
        return "IN"
    if transaction.transaction_type == "WITHDRAWAL":
        return "OUT"
    return "OUT" if transaction.source_account_id == account_id else "IN"


def transaction_table(
    transactions: Sequence[TransactionView], account_id: int
) -> tuple[list[str], list[list[object]]]:
    """Return headers and rows describing transactions relative to one account."""
    headers = ["ID", "Date (UTC)", "Type", "Direction", "Amount", "Status"]
    rows = []
    for transaction in transactions:
        moment = (
            transaction.created_at.astimezone(UTC)
            if transaction.created_at.tzinfo
            else transaction.created_at
        )
        rows.append(
            [
                transaction.transaction_id,
                moment.strftime("%Y-%m-%d %H:%M:%S"),
                transaction.transaction_type,
                _direction(transaction, account_id),
                transaction.amount,
                transaction.status,
            ]
        )
    return headers, rows
