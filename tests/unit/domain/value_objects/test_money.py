from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from banking.domain.value_objects.money import Money


@pytest.mark.parametrize(
    ("input_amount", "expected"),
    [
        ("1.004", Decimal("1.00")),
        ("1.005", Decimal("1.01")),
        ("-1.005", Decimal("-1.01")),
        ("0", Decimal("0.00")),
    ],
)
def test_money_quantizes_to_cents_with_half_up_rounding(
    input_amount: str, expected: Decimal
) -> None:
    assert Money(Decimal(input_amount)).amount == expected


@pytest.mark.parametrize("value", [1, 1.0, "1.00"])
def test_money_requires_decimal_instances(value: object) -> None:
    with pytest.raises(TypeError, match="Decimal"):
        Money(value)  


@pytest.mark.parametrize("value", [Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity")])
def test_money_rejects_non_finite_amounts(value: Decimal) -> None:
    with pytest.raises(ValueError, match="invalid"):
        Money(value)


def test_money_factory_zero_and_string_representation() -> None:
    assert Money.of("12.345").amount == Decimal("12.35")
    assert Money.of(Decimal(2)).amount == Decimal("2.00")
    assert Money.zero().amount == Decimal("0.00")
    assert str(Money.of("3")) == "3.00"


def test_money_factory_rejects_invalid_decimal_text() -> None:
    with pytest.raises(ValueError, match="Invalid amount"):
        Money.of("not-an-amount")


def test_money_factory_rejects_none_and_other_non_numeric_values() -> None:
    with pytest.raises(ValueError, match="Invalid amount"):
        Money.of(None)


def test_money_sign_checks_and_arithmetic() -> None:
    positive = Money.of("10.25")
    negative = Money.of("-2.50")
    zero = Money.zero()

    assert positive.is_positive()
    assert not positive.is_negative()
    assert negative.is_negative()
    assert not negative.is_positive()
    assert not zero.is_positive()
    assert not zero.is_negative()
    assert (positive + negative).amount == Decimal("7.75")
    assert (positive - Money.of("0.25")).amount == Decimal("10.00")


def test_money_comparison_operators() -> None:
    lower = Money.of("1.00")
    equal = Money.of("1.00")
    higher = Money.of("2.00")

    assert lower == equal
    assert lower < higher
    assert lower <= equal
    assert higher > lower
    assert higher >= equal


def test_money_is_immutable() -> None:
    money = Money.of("1")

    with pytest.raises(FrozenInstanceError):
        money.amount = Decimal(2) 
