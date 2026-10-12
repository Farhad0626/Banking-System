from dataclasses import dataclass


@dataclass(frozen=True)
class CardNumber:
    """Value object representing a card number."""

    value: str
