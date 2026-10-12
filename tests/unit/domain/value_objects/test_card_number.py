from dataclasses import FrozenInstanceError

import pytest

from banking.domain.value_objects.card_number import CardNumber


def test_card_number_stores_value_without_format_validation() -> None:
    assert CardNumber("not-validated").value == "not-validated"
    assert CardNumber("").value == ""


def test_card_number_is_immutable() -> None:
    number = CardNumber("1234")

    with pytest.raises(FrozenInstanceError):
        number.value = "5678"  
