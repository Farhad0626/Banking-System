from dataclasses import FrozenInstanceError

import pytest

from banking.domain.value_objects.customer_id import CustomerId


@pytest.mark.parametrize("value", [1, 42])
def test_customer_id_accepts_positive_values(value: int) -> None:
    assert CustomerId(value).value == value


@pytest.mark.parametrize("value", [0, -1])
def test_customer_id_rejects_non_positive_values(value: int) -> None:
    with pytest.raises(ValueError, match="must be positive"):
        CustomerId(value)


def test_customer_id_is_immutable() -> None:
    customer_id = CustomerId(1)

    with pytest.raises(FrozenInstanceError):
        customer_id.value = 2  
