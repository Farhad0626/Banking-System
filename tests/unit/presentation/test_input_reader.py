from datetime import UTC, datetime

import pytest

from banking.presentation.console.input_reader import InputCancelled, InputReader
from banking.presentation.console.output_writer import OutputWriter


def make_reader(values: list[str]) -> tuple[InputReader, list[str]]:
    messages: list[str] = []

    def read(prompt: str) -> str:
        assert values, f"Unexpected input request: {prompt}"
        return values.pop(0)

    return InputReader(OutputWriter(messages.append), input_fn=read), messages


def test_read_text_requires_value_and_normalizes_local_digits() -> None:
    reader, messages = make_reader(["  ", "۱۲۳۴۵"])

    assert reader.read_text("National ID", normalize_digits=True) == "12345"
    assert messages == ["[ERROR] This field is required."]


def test_read_text_uses_default_when_input_is_empty() -> None:
    reader, _ = make_reader([""])

    assert reader.read_text("Name", default="Ada") == "Ada"


def test_read_password_retries_empty_value_and_preserves_whitespace() -> None:
    messages: list[str] = []
    values = iter(["", "  Secret  "])
    reader = InputReader(
        OutputWriter(messages.append),
        password_fn=lambda _: next(values),
    )

    assert reader.read_password("Password") == "  Secret  "
    assert messages == ["[ERROR] Password cannot be empty."]


def test_read_choice_normalizes_persian_digits_and_rejects_invalid_input() -> None:
    reader, messages = make_reader(["9", "۲"])

    assert reader.read_choice("Select", ["1", "2"]) == "2"
    assert messages == ["[ERROR] Invalid choice. Valid options: 1, 2"]


def test_optional_choice_accepts_case_insensitive_value_and_enter() -> None:
    reader, messages = make_reader(["unknown", "deposit", ""])

    assert reader.read_optional_choice("Type", ["DEPOSIT", "WITHDRAW"]) == "DEPOSIT"
    assert reader.read_optional_choice("Type", ["DEPOSIT", "WITHDRAW"]) is None
    assert messages == [
        "[ERROR] Invalid value. Valid options: DEPOSIT, WITHDRAW (or Enter to skip)"
    ]


def test_read_amount_validates_scale_and_normalizes_decimal_digits() -> None:
    reader, messages = make_reader(["12.345", "۱۲٫۵۰"])

    assert reader.read_amount("Amount") == "12.50"
    assert messages == [
        "[ERROR] Enter a number with at most 2 decimal places (e.g. 150 or 150.50)."
    ]


def test_read_optional_date_retries_invalid_date_and_returns_utc_end_of_day() -> None:
    reader, messages = make_reader(["2026-02-30", "۲۰۲۶-02-28"])

    assert reader.read_optional_date("To date", end_of_day=True) == datetime(
        2026, 2, 28, 23, 59, 59, 999999, tzinfo=UTC
    )
    assert messages == ["[ERROR] Use the format YYYY-MM-DD (or press Enter to skip)."]


def test_read_methods_translate_eof_to_input_cancelled() -> None:
    reader = InputReader(OutputWriter(lambda *_: None), input_fn=lambda _: _raise_eof())

    with pytest.raises(InputCancelled):
        reader.read_text("Name")


def _raise_eof() -> str:
    raise EOFError
