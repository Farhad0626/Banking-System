from dataclasses import dataclass


@dataclass(frozen=True)
class CustomerId:
    """Value object representing a customer ID."""

    value: int

    def __post_init__(self) -> None:
        if not isinstance(self.value, int):
            raise TypeError("CustomerId must be an int.")
        if self.value <= 0:
            raise ValueError("CustomerId must be positive.")
