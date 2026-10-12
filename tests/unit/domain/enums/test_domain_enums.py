import pytest

from banking.domain.enums.account_status import AccountStatus
from banking.domain.enums.account_type import AccountType
from banking.domain.enums.card_status import CardStatus
from banking.domain.enums.transaction_status import TransactionStatus
from banking.domain.enums.transaction_type import TransactionType
from banking.domain.enums.user_role import UserRole


@pytest.mark.parametrize(
    ("enum_type", "expected"),
    [
        (AccountStatus, {"ACTIVE", "INACTIVE", "DELETED"}),
        (AccountType, {"SAVINGS", "CHECKING", "TERM_DEPOSIT"}),
        (CardStatus, {"ACTIVE", "BLOCKED"}),
        (TransactionStatus, {"PENDING", "COMPLETED", "FAILED"}),
        (TransactionType, {"DEPOSIT", "WITHDRAWAL", "TRANSFER"}),
        (UserRole, {"CUSTOMER", "ADMIN"}),
    ],
)
def test_enum_members_and_string_values(enum_type: type, expected: set[str]) -> None:
    assert {member.value for member in enum_type} == expected
    assert all(str(member) == f"{enum_type.__name__}.{member.name}" for member in enum_type)


def test_enum_values_can_be_compared_with_strings() -> None:
    assert AccountStatus.ACTIVE == "ACTIVE"
    assert TransactionType.TRANSFER == "TRANSFER"


def test_enum_construction_rejects_unknown_values() -> None:
    with pytest.raises(ValueError):
        AccountStatus("UNKNOWN")
