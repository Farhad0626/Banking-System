import pytest

from banking.domain.services.card_service import CardService


def test_issue_is_explicitly_unimplemented() -> None:
    with pytest.raises(NotImplementedError, match="out of scope"):
        CardService().issue()
