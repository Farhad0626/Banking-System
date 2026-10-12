from dataclasses import FrozenInstanceError

import pytest

from banking.domain.value_objects.account_number import AccountNumber


@pytest.mark.parametrize("value", ["0000000000000000", "1234567890123456"])
def test_account_number_accepts_exactly_16_ascii_digits(value: str) -> None:
    assert AccountNumber(value).value == value


@pytest.mark.parametrize(
    "value",
    [
        "",
        "123456789012345",
        "12345678901234567",
        "123456789012345a",
        "１２３４５６７８９０１２３４５６",
        " 123456789012345",
    ],
)
def test_account_number_rejects_invalid_formats(value: str) -> None:
    with pytest.raises(ValueError, match="valid format"):
        AccountNumber(value)


def test_account_number_is_immutable() -> None:
    number = AccountNumber("1234567890123456")

    with pytest.raises(FrozenInstanceError):
        number.value = "0000000000000000"  
