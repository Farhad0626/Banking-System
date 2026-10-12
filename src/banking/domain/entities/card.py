from dataclasses import dataclass


@dataclass
class Card:
    id: int
    account_id: int
    card_number: str
