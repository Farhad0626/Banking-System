from banking.domain.entities.card import Card


def test_card_stores_its_declared_fields() -> None:
    card = Card(id=7, account_id=3, card_number="card-value")

    assert (card.id, card.account_id, card.card_number) == (7, 3, "card-value")


def test_card_is_mutable() -> None:
    card = Card(id=7, account_id=3, card_number="old")

    card.card_number = "new"

    assert card.card_number == "new"
