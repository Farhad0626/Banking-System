import pytest

from banking.domain.services.fee_calculator import FeeCalculator


def test_calculate_fee_is_explicitly_unimplemented() -> None:
    with pytest.raises(NotImplementedError, match="out of scope"):
        FeeCalculator().calculate_fee()
