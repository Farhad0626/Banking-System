from banking.domain.enums.account_status import AccountStatus
from banking.domain.enums.transaction_type import TransactionType


def test_account_status_values():
    assert AccountStatus.ACTIVE.value == "ACTIVE"
    assert AccountStatus.INACTIVE.value == "INACTIVE"


def test_transaction_type_values():
    assert {t.value for t in TransactionType} == {"DEPOSIT", "WITHDRAWAL", "TRANSFER"}
