import pytest

from banking.domain.value_objects.account_number import AccountNumber
from banking.domain.value_objects.email import Email
from banking.domain.value_objects.national_id import NationalId
from banking.domain.value_objects.password import Password
from banking.domain.value_objects.phone_number import PhoneNumber


def test_password_accepts_baseline_rules_and_matches_username_case_insensitively() -> None:
    password = Password("Abcdefg1")

    assert password.matches_username("ABCDEFG1")
    assert not password.matches_username("different")


def test_password_accepts_minimum_length_and_maximum_utf8_byte_length() -> None:
    assert Password("A1aaaaaa").plain_value == "A1aaaaaa"
    assert len(Password("A1aaaaaa" + "x" * 64).plain_value.encode("utf-8")) == 72


@pytest.mark.parametrize(
    ("value", "strict", "message"),
    [
        ("Aa1", False, "at least 8"),
        ("abcdefgh1", False, "uppercase"),
        ("ABCDEFGH1", False, "lowercase"),
        ("Abcdefgh", False, "digit"),
        ("A1aaaaaa" + "x" * 65, False, "72 bytes"),
        ("Abcdefg1", True, "special character"),
    ],
)
def test_password_rejects_values_violating_configured_rules(
    value: str, strict: bool, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        Password(value, strict=strict)


def test_strict_password_accepts_supported_special_character() -> None:
    assert Password("Abcdefg1!", strict=True).strict


def test_password_limit_is_measured_in_utf8_bytes() -> None:
    assert len("Aa1" + "é" * 34) == 37
    assert len(("Aa1" + "é" * 34).encode("utf-8")) == 71
    assert Password("Aa1" + "é" * 34)

    with pytest.raises(ValueError, match="72 bytes"):
        Password("Aa1" + "é" * 35)


@pytest.mark.parametrize(
    ("factory", "message"),
    [
        (lambda: Password(None), "Password must be a string."),
        (lambda: NationalId(None), "National ID must be a string."),
        (lambda: PhoneNumber(None), "Phone number must be a string."),
        (lambda: Email(None), "Email must be a string."),
        (lambda: AccountNumber(None), "Account number must be a string."),
    ],
)
def test_value_objects_reject_non_string_inputs(factory: object, message: str) -> None:
    with pytest.raises(TypeError, match=message):
        factory()
