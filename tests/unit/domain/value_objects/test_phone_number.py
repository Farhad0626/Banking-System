from dataclasses import FrozenInstanceError

import pytest

from banking.domain.value_objects.phone_number import PhoneNumber


@pytest.mark.parametrize(
    "value",
    [
        "09123456789",
        "00989123456789",
        "+989123456789",
        "09901234567",
        "09951234567",
        "09101234567",
        "09191234567",
        "09201234567",
        "09231234567",
        "09301234567",
        "09391234567",
        "09961234567",
        "09991234567",
    ],
)
def test_phone_number_accepts_supported_prefix_formats(value: str) -> None:
    assert PhoneNumber(value).value == value


@pytest.mark.parametrize(
    "value",
    [
        "",
        "9123456789",
        "08123456789",
        "0912345678",
        "091234567890",
        "+98912345678",
        "0912345678a",
        "09123456789 ",
        "09241234567",
        "09401234567",
        "09891234567",
    ],
)
def test_phone_number_rejects_invalid_mobile_formats(value: str) -> None:
    with pytest.raises(ValueError, match="is invalid"):
        PhoneNumber(value)


def test_phone_number_is_immutable() -> None:
    phone = PhoneNumber("09123456789")

    with pytest.raises(FrozenInstanceError):
        phone.value = "09123456780"  
