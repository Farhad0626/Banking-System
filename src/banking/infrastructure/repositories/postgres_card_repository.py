from banking.application.ports.repositories.card_repository import CardRepository
from banking.domain.entities.card import Card


class PostgresCardRepository(CardRepository):
    """Skeleton for card persistence; intentionally not implemented in the Core Release."""

    def add(self, card: Card) -> None:
        """Not implemented: the Card subsystem is outside the Core Release."""
        raise NotImplementedError("Card subsystem is outside the Core Release.")
