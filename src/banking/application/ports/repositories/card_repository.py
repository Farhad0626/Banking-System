from abc import ABC, abstractmethod

from banking.domain.entities.card import Card


class CardRepository(ABC):
    """Abstract base class for card repository."""

    @abstractmethod
    def add(self, card: Card) -> None: ...
