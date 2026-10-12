from dataclasses import FrozenInstanceError

import pytest

from banking.domain.value_objects.email import Email


@pytest.mark.parametrize("value", ["a@example.com", "first.last+tag@sub.example.org"])
def test_email_accepts_values_matching_its_pattern(value: str) -> None:
    assert Email(value).value == value


@pytest.mark.parametrize(
    "value",
    ["", "plain-address", "user@localhost", "user@example.c", "user name@example.com"],
)
def test_email_rejects_values_outside_its_pattern(value: str) -> None:
    with pytest.raises(ValueError, match="is invalid"):
        Email(value)


def test_email_is_immutable() -> None:
    email = Email("a@example.com")

    with pytest.raises(FrozenInstanceError):
        email.value = "b@example.com"  
