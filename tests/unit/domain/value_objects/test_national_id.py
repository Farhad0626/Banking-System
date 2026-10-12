from dataclasses import FrozenInstanceError

import pytest

from banking.domain.value_objects.national_id import NationalId


def test_national_id_accepts_value_with_valid_check_digit() -> None:
    assert NationalId("1111111111").value == "1111111111"


@pytest.mark.parametrize("value", ["", "111111111", "11111111111", "1111111112", "abcdefghij"])
def test_national_id_rejects_invalid_length_digits_or_check_digit(value: str) -> None:
    with pytest.raises(ValueError, match="is invalid"):
        NationalId(value)


def test_national_id_is_immutable() -> None:
    national_id = NationalId("1111111111")

    with pytest.raises(FrozenInstanceError):
        national_id.value = "0000000000"  
