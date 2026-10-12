from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation


@dataclass(frozen=True, slots=True)
class Money:
    """The monetary amount is immutable. Always Decimal—never float."""

    amount: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            raise TypeError("Amount must be a Decimal instance not int or float.")
        if self.amount.is_nan() or self.amount.is_infinite():
            raise ValueError("Amount is invalid.")

        quantized = self.amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        object.__setattr__(self, "amount", quantized)

    @classmethod
    def of(cls, value: str | Decimal) -> Money:
        """Create a Money instance from a string representation of a decimal value."""
        try:
            return cls(Decimal(value))
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError(f"Invalid amount: {value}.")

    @classmethod
    def zero(cls) -> Money:
        """Create a Money instance representing zero."""
        return cls(Decimal(0))

    def is_positive(self) -> bool:
        return self.amount > 0

    def is_negative(self) -> bool:
        return self.amount < 0

    def __add__(self, other: Money) -> Money:
        if not isinstance(other, Money):
            return NotImplemented

        return Money(self.amount + other.amount)

    def __sub__(self, other: Money) -> Money:
        if not isinstance(other, Money):
            return NotImplemented

        return Money(self.amount - other.amount)

    def __lt__(self, other: Money) -> bool:
        if not isinstance(other, Money):
            return NotImplemented

        return self.amount < other.amount

    def __le__(self, other: Money) -> bool:
        if not isinstance(other, Money):
            return NotImplemented

        return self.amount <= other.amount

    def __gt__(self, other: Money) -> bool:
        if not isinstance(other, Money):
            return NotImplemented

        return self.amount > other.amount

    def __ge__(self, other: Money) -> bool:
        if not isinstance(other, Money):
            return NotImplemented

        return self.amount >= other.amount

    def __str__(self) -> str:
        return f"{self.amount:.2f}"
