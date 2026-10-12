from datetime import datetime, timedelta, timezone

from banking.application.dto.account.account_dto import AccountView
from banking.application.dto.customer.customer_dto import CustomerView
from banking.application.dto.transaction.transaction_dto import TransactionView
from banking.presentation.console.view_formatters import (
    account_table,
    customer_lines,
    transaction_table,
)


def test_account_table_numbers_rows_and_preserves_account_fields() -> None:
    headers, rows = account_table(
        [
            AccountView(8, 4, "0008", "SAVINGS", "25.00", "ACTIVE"),
            AccountView(9, 4, "0009", "CHECKING", "10.00", "ACTIVE"),
        ]
    )

    assert headers == ["#", "Account Number", "Type", "Balance", "Status"]
    assert rows == [
        [1, "0008", "SAVINGS", "25.00", "ACTIVE"],
        [2, "0009", "CHECKING", "10.00", "ACTIVE"],
    ]


def test_customer_lines_describes_status_without_exposing_secrets() -> None:
    lines = customer_lines(
        CustomerView(4, "Ada", "Lovelace", "123", "555", "ada@example.test", "ada", True, True)
    )

    assert ("Name", "Ada Lovelace") in lines
    assert ("Status", "Active (restricted)") in lines
    assert all("password" not in label.lower() for label, _ in lines)


def test_transaction_table_converts_time_to_utc_and_sets_directions() -> None:
    local_time = datetime(2026, 1, 2, 12, 0, tzinfo=timezone(timedelta(hours=3)))
    rows = [
        TransactionView(1, "DEPOSIT", "10.00", None, 4, "COMPLETED", local_time),
        TransactionView(2, "WITHDRAWAL", "2.00", 4, None, "COMPLETED", local_time),
        TransactionView(3, "TRANSFER", "3.00", 4, 5, "COMPLETED", local_time),
        TransactionView(4, "TRANSFER", "5.00", 5, 4, "COMPLETED", local_time),
    ]

    headers, rendered = transaction_table(rows, account_id=4)

    assert headers == ["ID", "Date (UTC)", "Type", "Direction", "Amount", "Status"]
    assert [row[3] for row in rendered] == ["IN", "OUT", "OUT", "IN"]
    assert all(row[1] == "2026-01-02 09:00:00" for row in rendered)
